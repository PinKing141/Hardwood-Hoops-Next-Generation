from typing import Dict, Iterable, Tuple

from courthoops.app.services.player_evaluation_service import PlayerEvaluationService
from courthoops.app.services.role_affinity_service import RoleAffinityService
from courthoops.domain.player.entity import Player


class AIDecisionService:
    """
    Provides AI-facing evaluations for lineup/contract/roster moves.
    Uses true OVR and role affinities; gameplay still uses granular attributes.
    """

    def __init__(
        self,
        evaluator: PlayerEvaluationService | None = None,
        role_affinity: RoleAffinityService | None = None,
    ):
        self.evaluator = evaluator or PlayerEvaluationService()
        self.role_affinity = role_affinity or RoleAffinityService()

    def evaluate_players(self, players: Iterable[Player], role_map: Dict[str, str] | None = None) -> Dict[str, Tuple[float, Dict[str, float]]]:
        role_map = role_map or {}
        true_ratings: Dict[str, Tuple[float, Dict[str, float]]] = {}
        for player in players:
            role = role_map.get(player.player_id, self.evaluator.default_role)
            true_ovr = self.evaluator.evaluate([player], role_map={player.player_id: role})[player.player_id][0]
            affinities = self.role_affinity.compute_affinities(player)
            true_ratings[player.player_id] = (true_ovr, affinities)
        return true_ratings
