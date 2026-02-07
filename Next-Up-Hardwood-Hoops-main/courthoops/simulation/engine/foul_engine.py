from typing import Callable, Optional, Dict

from courthoops.domain.game.events import Event
from courthoops.domain.game.possession import Possession
from courthoops.infra.utils.rng import IRNG
from courthoops.simulation.playbyplay.event_builder import EventBuilder
from courthoops.domain.player.entity import Player


class FoulEngine:
    """Handles foul determination and consequences."""

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

    def maybe_commit_foul(
        self,
        possession: Possession,
        defender_id: str | None = None,
        shooter_id: str | None = None,
        play_type: str | None = None,
        team_fouls: Optional[Dict[str, int]] = None,
    ) -> Optional[Event]:
        """Stochastic foul check influenced by defensive strength and bonus."""
        defense_strength = self.defense_strength_fn(possession.defense_team_id)
        offense_strength = self.offense_strength_fn(possession.offense_team_id)
        foul_prob = 0.08 + (offense_strength - defense_strength) / 300.0
        defender = self.player_lookup.get(defender_id) if defender_id else None
        if defender:
            foul_prob += (100 - defender.attributes.defensive_iq) / 1000.0
            foul_prob += (100 - defender.attributes.decision_discipline) / 1200.0
        foul_prob = min(max(foul_prob, 0.02), 0.2)
        if self.rng.random() >= foul_prob:
            return None
        desc = f"{possession.defense_team_id} commits a foul."
        shooting_foul = False
        ft_attempts = 0
        team_fouls = team_fouls or {}
        bonus = team_fouls.get(possession.defense_team_id, 0) >= 7  # simple single-bonus heuristic
        if bonus and self.rng.random() < 0.6:
            shooting_foul = True
            ft_attempts = 2
        elif self.rng.random() < 0.55:  # lean toward shooting fouls in this lightweight model
            shooting_foul = True
            # Simple heuristic: post/drive -> 2, spot-up sometimes 3
            if play_type == "spot_up" and self.rng.random() < 0.25:
                ft_attempts = 3
            else:
                ft_attempts = 2
        and_one = False
        if shooting_foul and self.rng.random() < 0.2:
            # mark as potential and-one if caller's shot was made
            and_one = True
        payload = {
            "team_id": possession.defense_team_id,
            "player_id": defender_id,
            "period": possession.period,
            "type": "personal",
            "shooting_foul": shooting_foul,
            "ft_attempts": ft_attempts,
            "fouled_player_id": shooter_id,
            "and_one": and_one,
        }
        return self.event_builder.build("foul", desc, payload)
