from typing import Dict, Iterable, List

from courthoops.app.services.player_evaluation_service import PlayerEvaluationService
from courthoops.app.services.role_affinity_service import RoleAffinityService
from courthoops.domain.player.entity import Player


class AIOpsService:
    """
    AI-facing helpers for lineup/depth chart and free-agent/transfer decisions using true OVR + role affinity.
    """

    def __init__(
        self,
        evaluator: PlayerEvaluationService | None = None,
        role_affinity: RoleAffinityService | None = None,
    ):
        self.evaluator = evaluator or PlayerEvaluationService()
        self.role_affinity = role_affinity or RoleAffinityService()

    def select_lineup(self, players: Iterable[Player], starters: int = 5, role_map: Dict[str, str] | None = None) -> Dict[str, List[Player]]:
        """
        Returns {"starters": [...], "bench": [...]}, sorted by true OVR.
        """
        ratings = self.evaluator.evaluate(players, role_map=role_map)
        sorted_players = sorted(players, key=lambda p: ratings[p.player_id][0], reverse=True)
        return {"starters": list(sorted_players[:starters]), "bench": list(sorted_players[starters:])}

    def rank_free_agents(self, players: Iterable[Player], role_map: Dict[str, str] | None = None) -> List[Player]:
        ratings = self.evaluator.evaluate(players, role_map=role_map)
        return sorted(players, key=lambda p: ratings[p.player_id][0], reverse=True)
