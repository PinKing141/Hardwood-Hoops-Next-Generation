from typing import Callable, Optional, Dict

from courthoops.domain.game.events import Event
from courthoops.domain.game.possession import Possession
from courthoops.infra.utils.rng import IRNG
from courthoops.simulation.playbyplay.event_builder import EventBuilder


class ShotEngine:
    """Resolves shot outcomes with probability based on lineup strength."""

    def __init__(
        self,
        rng: IRNG,
        offense_strength_fn: Callable[[str], float],
        defense_strength_fn: Callable[[str], float],
        player_lookup: Optional[Dict[str, object]] = None,
        event_builder: Optional[EventBuilder] = None,
    ):
        self.rng = rng
        self.offense_strength_fn = offense_strength_fn
        self.defense_strength_fn = defense_strength_fn
        self.player_lookup = player_lookup or {}
        self.event_builder = event_builder or EventBuilder()

    def resolve_shot(self, possession: Possession, shooter_id: str | None = None, assisted_by: str | None = None) -> Event:
        offense_strength = self.offense_strength_fn(possession.offense_team_id)
        defense_strength = self.defense_strength_fn(possession.defense_team_id)

        # Bias shot type by play_type: spot_up -> more threes, post_up -> fewer threes
        if possession.play_type == "spot_up":
            three_bias = 0.55
        elif possession.play_type == "post_up":
            three_bias = 0.1
        else:  # pnr or default
            three_bias = 0.35

        is_three = self.rng.random() < three_bias
        is_free_throw = False
        drew_and_one = False

        base_prob = 0.45 + (offense_strength - defense_strength) / 200.0
        if is_three:
            base_prob -= 0.05
        if possession.play_type == "post_up":
            base_prob += 0.02  # slight boost for close looks
        elif possession.play_type == "pnr":
            base_prob += 0.01
        base_prob += self._shooter_bonus(shooter_id, possession.play_type, is_three)
        # Attribute influence placeholders; caller can override strength_fn to include player-level detail
        make_prob = min(max(base_prob, 0.20), 0.8)
        made = self.rng.random() < make_prob
        points = 3 if is_three else 2

        # Occasional shooting fouls generating free throws
        if not made and self.rng.random() < 0.08:
            is_free_throw = True
            points = 1
            is_three = False

        event_type = "shot_made" if made else "shot_missed"
        desc = f"{possession.offense_team_id} {'drains' if made else 'misses'} a {points}-pt attempt."
        payload = {
            "team_id": possession.offense_team_id,
            "player_id": shooter_id,
            "assist_player_id": assisted_by if made else None,
            "points": points if made else 0,
            "period": possession.period,
            "is_three": is_three,
            "play_type": possession.play_type,
            "is_free_throw": is_free_throw,
            "and_one": drew_and_one,
        }
        return self.event_builder.build(event_type, desc, payload)

    def _shooter_bonus(self, shooter_id: Optional[str], play_type: Optional[str], is_three: bool) -> float:
        player = self.player_lookup.get(shooter_id) if shooter_id else None
        if not player:
            return 0.0
        attrs = getattr(player, "attributes", None)
        if not attrs:
            return 0.0
        bonus = 0.0
        if is_three:
            bonus += (attrs.three_point - 70) / 300.0
        elif play_type == "post_up":
            bonus += (attrs.inside - 70) / 300.0 + (attrs.dunk - 70) / 400.0
        else:  # pnr/spot midrange/inside
            bonus += (attrs.mid_range - 70) / 300.0 + (attrs.layup - 70) / 400.0
        return bonus
