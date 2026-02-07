from typing import Callable, Optional, Dict, List

from courthoops.domain.game.events import Event
from courthoops.domain.game.possession import Possession
from courthoops.infra.utils.rng import IRNG
from courthoops.simulation.playbyplay.event_builder import EventBuilder
from courthoops.domain.player.entity import Player


class ReboundEngine:
    """Resolves rebound outcomes after a missed shot."""

    def __init__(
        self,
        rng: IRNG,
        offense_strength_fn: Callable[[str], float],
        defense_strength_fn: Callable[[str], float],
        player_lookup: Optional[Dict[str, Player]] = None,
        event_builder: Optional[EventBuilder] = None,
    ):
        self.rng = rng
        self.offense_strength_fn = offense_strength_fn
        self.defense_strength_fn = defense_strength_fn
        self.player_lookup = player_lookup or {}
        self.event_builder = event_builder or EventBuilder()

    def resolve_rebound(
        self,
        possession: Possession,
        rebounder_id: str | None = None,
        offense_lineup: Optional[list[str]] = None,
        defense_lineup: Optional[list[str]] = None,
        fatigue_by_player: Optional[Dict[str, float]] = None,
        fouls_by_player: Optional[Dict[str, int]] = None,
    ) -> Event:
        offense_strength = self.offense_strength_fn(possession.offense_team_id)
        defense_strength = self.defense_strength_fn(possession.defense_team_id)
        off_reb_prob = 0.25 + (offense_strength - defense_strength) / 300.0

        offense_ids = offense_lineup or []
        defense_ids = defense_lineup or []
        fatigue = fatigue_by_player or {}
        fouls = fouls_by_player or {}

        # Lineup average rebounding nudges
        off_avg = self._avg_rebound(offense_ids, offense=True, fatigue=fatigue, fouls=fouls)
        def_avg = self._avg_rebound(defense_ids, offense=False, fatigue=fatigue, fouls=fouls)
        off_reb_prob += (off_avg - def_avg) / 800.0

        # If a rebounder was targeted (e.g., block deflection), bias toward their side
        if rebounder_id:
            if rebounder_id in offense_ids:
                off_reb_prob += self._rebound_bonus(rebounder_id, offense=True, fatigue=fatigue, fouls=fouls)
            elif rebounder_id in defense_ids:
                off_reb_prob -= self._rebound_bonus(rebounder_id, offense=False, fatigue=fatigue, fouls=fouls)

        off_reb_prob = min(max(off_reb_prob, 0.1), 0.6)
        offense_board = self.rng.random() < off_reb_prob
        rebound_side = offense_ids if offense_board else defense_ids
        chosen_rebounder = (
            self._pick_rebounder(rebound_side, offense=offense_board, fatigue=fatigue, fouls=fouls) or rebounder_id
        )

        team = possession.offense_team_id if offense_board else possession.defense_team_id
        desc = f"{team} controls the rebound."
        return self.event_builder.build(
            "rebound",
            desc,
            {"team_id": team, "player_id": chosen_rebounder, "period": possession.period},
        )

    def _rebound_bonus(self, pid: str, offense: bool, fatigue: Dict[str, float], fouls: Dict[str, int]) -> float:
        player = self.player_lookup.get(pid)
        if not player:
            return 0.0
        fatigue_penalty = fatigue.get(pid, 0.0) * 0.003
        foul_penalty = max(fouls.get(pid, 0) - 3, 0) * 0.03
        intent = self._rebound_intent_multiplier(player, offense)
        if offense:
            return (player.attributes.offensive_rebound - 70) / 500.0 * intent - fatigue_penalty - foul_penalty
        return (player.attributes.defensive_rebound - 70) / 500.0 * intent - fatigue_penalty - foul_penalty

    def _avg_rebound(self, ids: List[str], offense: bool, fatigue: Dict[str, float], fouls: Dict[str, int]) -> float:
        if not ids:
            return 0.0
        total = 0.0
        for pid in ids:
            player = self.player_lookup.get(pid)
            if not player:
                continue
            attrs = player.attributes
            base = attrs.offensive_rebound if offense else attrs.defensive_rebound
            base += (attrs.vertical - 50) * 0.2 + (attrs.strength - 50) * 0.15
            base -= fatigue.get(pid, 0.0) * 0.2
            base *= self._rebound_intent_multiplier(player, offense)
            base -= max(fouls.get(pid, 0) - 3, 0) * 1.5
            total += base
        return total / max(len(ids), 1)

    def _pick_rebounder(self, ids: List[str], offense: bool, fatigue: Dict[str, float], fouls: Dict[str, int]) -> Optional[str]:
        if not ids:
            return None
        weights = []
        for pid in ids:
            player = self.player_lookup.get(pid)
            if not player:
                weights.append(1.0)
                continue
            attrs = player.attributes
            base = attrs.offensive_rebound if offense else attrs.defensive_rebound
            base += (attrs.vertical - 50) * 0.4 + (attrs.strength - 50) * 0.25
            base -= fatigue.get(pid, 0.0) * 0.3
            base *= self._rebound_intent_multiplier(player, offense)
            base -= max(fouls.get(pid, 0) - 3, 0) * 2.0
            weights.append(max(base, 1.0))
        return self.rng.choice_weighted(ids, weights)

    def _rebound_intent_multiplier(self, player: Player, offense: bool) -> float:
        tendencies = getattr(player, "tendencies", None)
        if not tendencies or not getattr(tendencies, "rebound_bias", None):
            return 1.0
        crash, leak, balanced = tendencies.rebound_bias
        if offense:
            return 1.0 + crash * 0.4 - leak * 0.3
        # Defense: crash == box out intent, leak reduces presence
        return 1.0 + crash * 0.25 - leak * 0.35
