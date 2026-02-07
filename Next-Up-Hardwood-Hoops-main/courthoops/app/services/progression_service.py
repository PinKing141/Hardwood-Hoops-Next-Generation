from typing import Dict, Iterable

from courthoops.app.services.role_affinity_service import RoleAffinityService
from courthoops.domain.player.entity import Player


class ProgressionService:
    """
    Applies soft caps via role affinities to shape growth without locking archetypes.
    """

    def __init__(
        self,
        role_affinity: RoleAffinityService | None = None,
        max_growth: float = 2.5,
        decline_start_age: int = 24,
        decline_rate: float = 1.0,
        position_decline: Dict[str, float] | None = None,
    ):
        self.role_affinity = role_affinity or RoleAffinityService()
        self.max_growth = max_growth
        self.decline_start_age = decline_start_age
        self.decline_rate = decline_rate
        self.position_decline = position_decline or {
            "guard": 1.0,
            "wing": 1.0,
            "forward": 1.05,
            "center": 1.1,
        }

    def apply_growth(self, players: Iterable[Player], position_map: Dict[str, str] | None = None) -> None:
        for player in players:
            affinities = self.role_affinity.compute_affinities(player)
            primary = max(affinities, key=affinities.get) if affinities else None
            soft_caps = self._role_soft_caps().get(primary, {})
            # Growth modifier from potential/consistency/decision_discipline
            attr_mod = (player.attributes.potential - 50) / 100.0
            consistency_mod = (player.attributes.consistency - 50) / 200.0
            discipline_mod = (player.attributes.decision_discipline - 50) / 200.0
            growth_scalar = max(0.5, 1.0 + attr_mod + consistency_mod + discipline_mod)
            for attr, cap in soft_caps.items():
                current = getattr(player.attributes, attr, 50)
                if current >= cap:
                    # beyond soft cap: slower growth
                    growth = min(0.5, self.max_growth * 0.2) * growth_scalar
                else:
                    growth = min(self.max_growth, cap - current) * growth_scalar
                setattr(player.attributes, attr, min(99, current + growth))

            # Age-based decline after threshold
            age = self._age_from_class_year(player.class_year)
            if age and age >= self.decline_start_age:
                pos = (position_map or {}).get(player.player_id, "").lower()
                pos_factor = self.position_decline.get(pos, 1.0)
                decline_amount = self.decline_rate * pos_factor * ((age - self.decline_start_age + 1) * 0.2)
                for attr in ("speed", "agility", "vertical", "stamina", "strength"):
                    val = getattr(player.attributes, attr, 50)
                    setattr(player.attributes, attr, max(25, val - decline_amount))

    def _age_from_class_year(self, class_year: str) -> int | None:
        mapping = {"FR": 18, "SO": 19, "JR": 20, "SR": 21}
        if not class_year:
            return None
        # Class year may include prefix like HS/College; grab trailing token
        token = class_year.split()[-1]
        return mapping.get(token, None)

    def _role_soft_caps(self) -> Dict[str, Dict[str, float]]:
        return {
            "rim_pressure_wing": {"dunk": 92, "speed": 90, "perimeter_defense": 85},
            "spot_up_shooter": {"three_point": 95, "free_throw": 92, "perimeter_defense": 80},
            "primary_creator": {"ball_control": 95, "passing": 95, "speed": 90},
            "secondary_creator": {"ball_control": 90, "passing": 90, "three_point": 90},
            "stretch_big": {"three_point": 90, "mid_range": 90, "defensive_rebound": 85},
            "glass_cleaner": {"defensive_rebound": 95, "offensive_rebound": 92, "strength": 90},
            "defensive_stopper": {"perimeter_defense": 95, "interior_defense": 90, "steal": 90, "block": 90},
        }
