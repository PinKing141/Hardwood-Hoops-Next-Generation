from typing import Dict, Iterable, Tuple

from courthoops.domain.player.entity import Player
from courthoops.domain.player.overall import compute_public_overall, compute_true_overall


class PlayerEvaluationService:
    """
    Computes true/public overalls for players.
    True OVR: hidden, AI-facing.
    Public OVR: slightly noisy, UI/scouting-facing.
    Gameplay must continue to use granular attributes.
    """

    def __init__(self, default_role: str = "wing"):
        self.default_role = default_role

    def evaluate(self, players: Iterable[Player], role_map: Dict[str, str] | None = None) -> Dict[str, Tuple[float, float]]:
        role_map = role_map or {}
        ratings: Dict[str, Tuple[float, float]] = {}
        for player in players:
            role = role_map.get(player.player_id, self.default_role)
            true_ovr, public_ovr = compute_public_overall(player, role=role)
            ratings[player.player_id] = (true_ovr, public_ovr)
        return ratings

    def best_players(self, players: Iterable[Player], top_n: int = 10, role_map: Dict[str, str] | None = None) -> list[Player]:
        role_map = role_map or {}
        scored = []
        for player in players:
            role = role_map.get(player.player_id, self.default_role)
            true_ovr = compute_true_overall(player, role=role)
            scored.append((true_ovr, player))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [p for _, p in scored[:top_n]]
