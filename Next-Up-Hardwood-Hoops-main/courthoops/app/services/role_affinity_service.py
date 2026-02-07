from typing import Dict, Iterable

from courthoops.domain.player.entity import Player


class RoleAffinityService:
    """
    Derives soft role affinities from attributes + tendencies.
    Affinities are continuous weights; no hard assignments.
    """

    def __init__(self):
        self.role_vectors = self._default_role_vectors()

    def compute_affinities(self, player: Player) -> Dict[str, float]:
        t = player.tendencies
        attrs = player.attributes
        affinities: Dict[str, float] = {}

        for role, vec in self.role_vectors.items():
            score = 0.0
            score += vec.get("shot_close", 0.0) * t.shot_profile[0]
            score += vec.get("shot_mid", 0.0) * t.shot_profile[1]
            score += vec.get("shot_three", 0.0) * t.shot_profile[2]
            score += vec.get("rim_dunk", 0.0) * t.rim_aggression[1]
            score += vec.get("creation_drive", 0.0) * t.shot_creation[2]
            score += vec.get("creation_catch", 0.0) * t.shot_creation[0]
            score += vec.get("playmaking_pass", 0.0) * t.playmaking_bias[1]
            score += vec.get("defense_disrupt", 0.0) * t.defensive_style[1]
            score += vec.get("defense_gamble", 0.0) * t.defensive_style[2]
            score += vec.get("help_early", 0.0) * t.help_defense[0]
            score += vec.get("rebound_crash", 0.0) * t.rebound_bias[0]
            score += vec.get("athletic_straight", 0.0) * t.athletic_usage[0]
            score += vec.get("athletic_vertical", 0.0) * t.athletic_usage[2]
            # Attribute touches
            score += vec.get("finishing", 0.0) * (attrs.layup + attrs.dunk + attrs.inside) / 300.0
            score += vec.get("shooting", 0.0) * (attrs.mid_range + attrs.three_point + attrs.free_throw) / 300.0
            score += vec.get("playmaking_attr", 0.0) * (attrs.ball_control + attrs.passing) / 200.0
            score += vec.get("defense_attr", 0.0) * (attrs.perimeter_defense + attrs.interior_defense + attrs.steal + attrs.block) / 400.0
            score += vec.get("rebounding_attr", 0.0) * (attrs.offensive_rebound + attrs.defensive_rebound) / 200.0
            score += vec.get("athletic_attr", 0.0) * (attrs.speed + attrs.agility + attrs.vertical) / 300.0
            affinities[role] = score

        # Normalize affinities so they sum to 1.0 for easier comparison
        total = sum(affinities.values())
        if total > 0:
            for k in affinities:
                affinities[k] /= total
        return affinities

    def compute_affinities_for_ids(self, player_ids: Iterable[str], player_lookup: Dict[str, Player] | None = None) -> Dict[str, Dict[str, float]]:
        """Utility to compute affinities for a list of player ids when a lookup is available."""
        lookup = player_lookup or getattr(self, "player_lookup", {})
        return {pid: self.compute_affinities(lookup[pid]) for pid in player_ids if pid in lookup}

    def top_roles(self, player: Player, n: int = 3) -> Dict[str, float]:
        aff = self.compute_affinities(player)
        return dict(sorted(aff.items(), key=lambda kv: kv[1], reverse=True)[:n])

    @staticmethod
    def _default_role_vectors() -> Dict[str, Dict[str, float]]:
        """
        Role gravity vectors. Values are relative weights for matching tendencies/attributes.
        These are intentionally soft and do not enforce archetypes.
        """
        return {
            "rim_pressure_wing": {
                "shot_close": 0.25,
                "shot_mid": 0.1,
                "shot_three": 0.05,
                "rim_dunk": 0.25,
                "creation_drive": 0.25,
                "athletic_straight": 0.05,
                "athletic_vertical": 0.05,
                "finishing": 0.2,
                "athletic_attr": 0.1,
            },
            "spot_up_shooter": {
                "shot_close": 0.05,
                "shot_mid": 0.15,
                "shot_three": 0.35,
                "creation_catch": 0.25,
                "playmaking_pass": 0.05,
                "shooting": 0.25,
            },
            "secondary_creator": {
                "shot_mid": 0.15,
                "shot_three": 0.15,
                "creation_drive": 0.2,
                "creation_catch": 0.1,
                "playmaking_pass": 0.25,
                "playmaking_attr": 0.25,
            },
            "primary_creator": {
                "creation_drive": 0.25,
                "creation_catch": 0.1,
                "shot_mid": 0.1,
                "shot_three": 0.1,
                "playmaking_pass": 0.25,
                "playmaking_attr": 0.25,
                "athletic_straight": 0.05,
            },
            "defensive_stopper": {
                "defense_disrupt": 0.2,
                "defense_gamble": 0.05,
                "help_early": 0.15,
                "rebound_crash": 0.1,
                "defense_attr": 0.35,
                "athletic_attr": 0.15,
            },
            "glass_cleaner": {
                "rebound_crash": 0.35,
                "athletic_vertical": 0.1,
                "finishing": 0.1,
                "rebounding_attr": 0.35,
                "defense_attr": 0.1,
            },
            "stretch_big": {
                "shot_mid": 0.15,
                "shot_three": 0.3,
                "creation_catch": 0.2,
                "rebound_crash": 0.1,
                "shooting": 0.25,
            },
        }
