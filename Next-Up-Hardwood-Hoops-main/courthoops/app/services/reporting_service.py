from typing import Dict, Iterable, List

from courthoops.domain.game.boxscore import BoxScore
from courthoops.domain.recruiting.models import RecruitingInterest
from courthoops.domain.player.entity import Player


class ReportingService:
    """Helper to shape data for UI/CLI injury reports and box score views."""

    def injury_report(self, players: Iterable[Player]) -> List[dict]:
        report: List[dict] = []
        for p in players:
            if not p.injured:
                continue
            report.append(
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "status": p.injury_status or "injured",
                    "severity": p.injury_severity,
                    "injury_type": p.injury_type,
                    "days_remaining": p.injury_days,
                }
            )
        return report

    def boxscore_views(self, box_scores: Iterable[BoxScore]) -> List[dict]:
        views: List[dict] = []
        for box in box_scores:
            payload = box.payload or {}
            views.append(
                {
                    "game_id": box.game_id,
                    "home_team_id": box.home_team_id,
                    "away_team_id": box.away_team_id,
                    "home_score": box.home_score,
                    "away_score": box.away_score,
                    "players": payload.get("players", {}),
                    "teams": payload.get("teams", {}),
                }
            )
        return views

    def prospect_board_view(self, interactions: Iterable[RecruitingInterest], ai: bool = False) -> List[dict]:
        board = []
        for inter in interactions:
            board.append(
                {
                    "player_id": inter.player_id,
                    "team_id": inter.team_id,
                    "public_rating": inter.public_rating,
                    "true_rating": inter.true_rating if ai else None,
                    "class_rank": inter.class_rank,
                    "interest": inter.interest,
                    "committed": inter.committed,
                    "visits": inter.visits,
                    "visit_history": inter.visit_history,
                    "offer_history": inter.offer_history,
                }
            )
        return board
