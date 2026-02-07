import random
from typing import Dict, Iterable, List, Tuple

from courthoops.domain.player.entity import Player


class InjuryService:
    """
    Applies injury checks based on injury_proneness and fatigue.
    Can be used per-game or per-season.
    """

    def __init__(self, base_rate: float = 0.01):
        self.base_rate = base_rate

    INJURY_CATALOG = [
        {"name": "ankle sprain", "severity": "day-to-day", "min_days": 1, "max_days": 3},
        {"name": "concussion protocol", "severity": "day-to-day", "min_days": 1, "max_days": 6},
        {"name": "hamstring tweak", "severity": "short-term", "min_days": 3, "max_days": 8},
        {"name": "shoulder strain", "severity": "short-term", "min_days": 4, "max_days": 10},
        {"name": "knee sprain", "severity": "multi-week", "min_days": 10, "max_days": 21},
        {"name": "stress fracture", "severity": "long-term", "min_days": 21, "max_days": 45},
    ]

    def apply_game_injuries(self, players: Iterable[Player], fatigue_by_player: Dict[str, float]) -> Dict[str, int]:
        """
        Returns a dict of player_id -> injury_days (0 means no new injury).
        Injury duration scales with injury proneness and fatigue.
        """
        injuries: Dict[str, int] = {}
        for player in players:
            fatigue = fatigue_by_player.get(player.player_id, 0.0)
            # Injury chance scales with proneness and fatigue
            chance = self.base_rate + (player.attributes.injury_proneness / 100.0) * 0.02 + (fatigue / 100.0) * 0.01
            if random.random() < chance:
                duration, injury_type, severity = self._assign_injury(player, fatigue)
                injuries[player.player_id] = duration
                player.injured = True
                player.injury_days = duration
                player.injury_type = injury_type
                player.injury_severity = severity
                player.injury_status = f"{severity} ({injury_type}, {duration}d)"
        return injuries

    def apply_season_recovery(self, players: Iterable[Player]) -> Dict[str, bool]:
        """Simple recovery: high work_ethic and lower injury_proneness recover faster."""
        recovered: Dict[str, bool] = {}
        for player in players:
            if not player.injured and player.injury_days <= 0:
                recovered[player.player_id] = False
                continue
            # decrement injury days and check if recovered
            player.injury_days = max(player.injury_days - 1, 0)
            chance = 0.5 + (1 - player.attributes.injury_proneness / 100.0) * 0.3 + player.personality.work_ethic * 0.2
            recovered_now = player.injury_days == 0 and random.random() < chance
            if recovered_now:
                player.injured = False
                player.injury_type = None
                player.injury_severity = None
                player.injury_status = None
            else:
                # Update status text with remaining days
                player.injury_status = f"{player.injury_severity or 'injured'} ({player.injury_type or 'injury'}, {player.injury_days}d)"
            recovered[player.player_id] = recovered_now
        return recovered

    def _assign_injury(self, player: Player, fatigue: float) -> Tuple[int, str, str]:
        severity_bias = (player.attributes.injury_proneness / 100.0) * 0.5 + (fatigue / 100.0) * 0.35
        weights = []
        for entry in self.INJURY_CATALOG:
            tier = {"day-to-day": 0, "short-term": 1, "multi-week": 2, "long-term": 3}.get(entry["severity"], 1)
            base = {0: 1.0, 1: 0.7, 2: 0.4, 3: 0.2}[tier]
            weights.append(base * (1.0 + severity_bias * (0.3 + 0.25 * tier)))
        entry = random.choices(self.INJURY_CATALOG, weights=weights, k=1)[0]
        dur_min, dur_max = entry["min_days"], entry["max_days"]
        # scale duration slightly by proneness (up to +30%) and randomness
        scale = 1.0 + (player.attributes.injury_proneness / 100.0) * 0.3
        duration = int(random.randint(dur_min, dur_max) * scale)
        duration = max(duration, 1)
        return duration, entry["name"], entry["severity"]
