from typing import Dict, Iterable, List

from courthoops.app.services.build_name_service import BuildNameService
from courthoops.app.services.player_evaluation_service import PlayerEvaluationService
from courthoops.app.services.role_affinity_service import RoleAffinityService
from courthoops.domain.recruiting.models import RecruitingInterest
from courthoops.domain.player.entity import Player


class ScoutingService:
    """
    Combines public OVR, build name, and top role descriptors for UI/scouting views.
    Gameplay should still rely on granular attributes and tendencies.
    """

    def __init__(
        self,
        evaluator: PlayerEvaluationService | None = None,
        build_namer: BuildNameService | None = None,
        role_affinity: RoleAffinityService | None = None,
    ):
        self.evaluator = evaluator or PlayerEvaluationService()
        self.build_namer = build_namer or BuildNameService()
        self.role_affinity = role_affinity or RoleAffinityService()

    def scouting_reports(
        self,
        players: Iterable[Player],
        role_map: Dict[str, str] | None = None,
        recruiting: Dict[str, RecruitingInterest] | None = None,
    ) -> Dict[str, dict]:
        ratings = self.evaluator.evaluate(players, role_map=role_map)
        reports: Dict[str, dict] = {}
        for player in players:
            _, public_ovr = ratings[player.player_id]
            build_name = self.build_namer.generate_name(player)
            top_roles = list(self.role_affinity.top_roles(player, n=3).keys())
            status = "injured" if player.injured else "healthy"
            if player.injured and getattr(player, "injury_days", 0):
                status = f"injured ({player.injury_days}d)"
            rec = recruiting.get(player.player_id) if recruiting else None
            reports[player.player_id] = {
                "public_ovr": round(public_ovr, 1),
                "build_name": build_name,
                "role_descriptors": top_roles,
                "status": status,
                "class_rank": getattr(rec, "class_rank", None) if rec else None,
                "public_rating": getattr(rec, "public_rating", None) if rec else None,
                "visits": getattr(rec, "visits", None) if rec else None,
                "offers": len(rec.offer_history) if rec and getattr(rec, "offer_history", None) else None,
                "visited_weeks": rec.visit_history if rec else None,
            }
        return reports
