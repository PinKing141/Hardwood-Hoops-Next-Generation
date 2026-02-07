from typing import Iterable, Optional, Dict

from courthoops.domain.game.events import Event
from courthoops.domain.game.possession import Possession
from courthoops.simulation.engine.foul_engine import FoulEngine
from courthoops.simulation.engine.rebound_engine import ReboundEngine
from courthoops.simulation.engine.shot_engine import ShotEngine
from courthoops.app.services.role_affinity_service import RoleAffinityService
from courthoops.domain.player.entity import Player


class PossessionEngine:
    """Selects a play and dispatches shot/rebound/foul resolution."""

    def __init__(
        self,
        shot_engine: ShotEngine,
        rebound_engine: Optional[ReboundEngine] = None,
        foul_engine: Optional[FoulEngine] = None,
        role_affinity: Optional[RoleAffinityService] = None,
        player_lookup: Optional[Dict[str, Player]] = None,
    ):
        self.shot_engine = shot_engine
        self.rebound_engine = rebound_engine
        self.foul_engine = foul_engine
        self.role_affinity = role_affinity or RoleAffinityService()
        self.player_lookup = player_lookup or {}

    def run_possession(
        self,
        possession: Possession,
        offense_lineup: list[str],
        defense_lineup: list[str],
        fatigue_by_player: Optional[Dict[str, float]] = None,
        fouls_by_player: Optional[Dict[str, int]] = None,
    ) -> Iterable[Event]:
        """Lightweight possession: select a play based on tendencies, attempt shot, maybe a foul, maybe a rebound."""
        rng = getattr(self.shot_engine, "rng", None)
        play_type, shooter = self._select_play_and_shooter(offense_lineup, rng)
        assisted_by = None
        if rng and offense_lineup and len(offense_lineup) > 1 and rng.random() < (0.5 if play_type in ("spot_up", "pnr") else 0.3):
            assisted_by = rng.choice([pid for pid in offense_lineup if pid != shooter])

        defender = rng.choice(defense_lineup) if rng and defense_lineup else (defense_lineup[0] if defense_lineup else None)
        # Pre-shot steal / turnover chance
        if rng and defense_lineup and offense_lineup:
            steal_chance = 0.05 + self._steal_bonus(defender)
            if rng.random() < steal_chance:
                stealer = defender or rng.choice(defense_lineup)
                yield self._build_event("steal", possession, team_id=possession.defense_team_id, player_id=stealer)
                yield self._build_event("turnover", possession, team_id=possession.offense_team_id, player_id=shooter)
                return

        foul = None
        if self.foul_engine:
            foul = self.foul_engine.maybe_commit_foul(
                possession,
                defender_id=defender,
                shooter_id=shooter,
                play_type=play_type,
                team_fouls=getattr(self, "_team_fouls", None),
            )
        if foul:
            yield foul
            payload = getattr(foul, "payload", {}) or {}
            if payload.get("shooting_foul"):
                attempts = payload.get("ft_attempts", 2) or 2
                fouled = payload.get("fouled_player_id") or shooter
                for _ in range(attempts):
                    ft_event = self._shoot_free_throw(possession, fouled, rng)
                    yield ft_event
                # and-one if shot already made and foul tied to shooter
                if payload.get("and_one_shot_made"):
                    bonus_event = self._shoot_free_throw(possession, fouled, rng)
                    yield bonus_event
                return
            return

        shot_event = self.shot_engine.resolve_shot(possession, shooter_id=shooter, assisted_by=assisted_by)
        yield shot_event

        blocked_event: Event | None = None
        if shot_event.event_type == "shot_missed" and defense_lineup and rng:
            block_chance = 0.1 + self._block_bonus(defender)
            if rng.random() < block_chance:
                blocker = defender or rng.choice(defense_lineup)
                blocked_event = self._build_event("block", possession, team_id=possession.defense_team_id, player_id=blocker)

        if blocked_event:
            yield blocked_event

        if shot_event.event_type == "shot_missed" and self.rebound_engine:
            rebounder_pool = offense_lineup if rng and rng.random() < 0.25 else defense_lineup
            rebounder = rng.choice(rebounder_pool) if rng and rebounder_pool else (rebounder_pool[0] if rebounder_pool else None)
            rebound = self.rebound_engine.resolve_rebound(
                possession,
                rebounder_id=rebounder,
                offense_lineup=offense_lineup,
                defense_lineup=defense_lineup,
                fatigue_by_player=fatigue_by_player,
                fouls_by_player=fouls_by_player or {},
            )
            yield rebound

    def _select_play_and_shooter(self, offense_lineup: list[str], rng) -> tuple[str, str | None]:
        if not offense_lineup:
            return "spot_up", None
        shooter = self._weighted_shooter_choice(offense_lineup, rng)
        play_types = ["pnr", "post_up", "spot_up"]

        # Use role affinities + tendencies to weight play types
        affinities = self.role_affinity.compute_affinities_for_ids(offense_lineup, player_lookup=self.player_lookup)
        shooter_aff = affinities.get(shooter, {})

        shooter_obj = self.player_lookup.get(shooter)
        shot_profile = getattr(shooter_obj.tendencies, "shot_profile", [0.4, 0.25, 0.35]) if shooter_obj else [0.4, 0.25, 0.35]
        rim_aggression = getattr(shooter_obj.tendencies, "rim_aggression", [0.6, 0.4]) if shooter_obj else [0.6, 0.4]
        creation = getattr(shooter_obj.tendencies, "shot_creation", [0.4, 0.25, 0.35]) if shooter_obj else [0.4, 0.25, 0.35]

        spot_weight = shooter_aff.get("spot_up_shooter", 0.2) + 0.2 + shot_profile[2] * 0.5 + creation[0] * 0.3
        pnr_weight = shooter_aff.get("primary_creator", 0.2) + 0.2 + creation[2] * 0.4
        post_weight = shooter_aff.get("stretch_big", 0.1) + shooter_aff.get("glass_cleaner", 0.1) + shot_profile[0] * 0.4 + rim_aggression[1] * 0.2

        play_weights = [pnr_weight, post_weight, spot_weight]
        play_type = rng.choice_weighted(play_types, play_weights) if rng else play_types[0]
        return play_type, shooter

    def _weighted_shooter_choice(self, offense_lineup: list[str], rng) -> str:
        if not offense_lineup:
            return ""
        if not rng:
            return offense_lineup[0]
        weights = []
        for pid in offense_lineup:
            player = self.player_lookup.get(pid)
            if player:
                attrs = player.attributes
                tendencies = player.tendencies
                weight = (
                    tendencies.shot_profile[2] * attrs.three_point
                    + tendencies.shot_profile[0] * (attrs.inside + attrs.dunk)
                    + tendencies.shot_profile[1] * attrs.mid_range
                )
            else:
                weight = 50
            weights.append(weight or 1.0)
        return rng.choice_weighted(offense_lineup, weights)

    def _steal_bonus(self, defender_id: Optional[str]) -> float:
        defender = self.player_lookup.get(defender_id) if defender_id else None
        if not defender:
            return 0.0
        attrs = defender.attributes
        return (attrs.steal - 70) / 500.0

    def _block_bonus(self, defender_id: Optional[str]) -> float:
        defender = self.player_lookup.get(defender_id) if defender_id else None
        if not defender:
            return 0.0
        attrs = defender.attributes
        return (attrs.block - 70) / 500.0 + (attrs.vertical - 70) / 800.0

    def _build_event(self, event_type: str, possession: Possession, team_id: str | None = None, player_id: str | None = None) -> Event:
        from courthoops.simulation.playbyplay.event_builder import EventBuilder

        builder = EventBuilder()
        desc = event_type.replace("_", " ").title()
        return builder.build(event_type, desc, {"team_id": team_id, "player_id": player_id, "period": possession.period})

    def _shoot_free_throw(self, possession: Possession, shooter_id: Optional[str], rng) -> Event:
        from courthoops.simulation.playbyplay.event_builder import EventBuilder

        builder = EventBuilder()
        make_prob = 0.75
        player = self.player_lookup.get(shooter_id) if shooter_id else None
        if player:
            make_prob = min(max((player.attributes.free_throw - 40) / 80.0, 0.5), 0.95)
        made = rng.random() < make_prob if rng else True
        event_type = "shot_made" if made else "shot_missed"
        desc = f"{possession.offense_team_id} {'makes' if made else 'misses'} a free throw."
        payload = {
            "team_id": possession.offense_team_id,
            "player_id": shooter_id,
            "assist_player_id": None,
            "points": 1 if made else 0,
            "period": possession.period,
            "is_three": False,
            "play_type": "free_throw",
            "is_free_throw": True,
        }
        return builder.build(event_type, desc, payload)
