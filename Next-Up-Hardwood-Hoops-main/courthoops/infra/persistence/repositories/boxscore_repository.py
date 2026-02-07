from typing import Callable, Optional

from sqlalchemy.orm import Session

from courthoops.domain.game.boxscore import BoxScore
from courthoops.infra.persistence.orm.models import BoxScoreRow


class BoxScoreRepository:
    """Persists box scores for quick season queries."""

    def __init__(self, session_factory: Callable[[], Session], universe_id: str = "UNIVERSE"):
        self._session_factory = session_factory
        self.universe_id = universe_id

    def save(self, box: BoxScore, payload: Optional[dict] = None) -> None:
        with self._session_factory() as session:
            row = (
                session.query(BoxScoreRow)
                .filter(BoxScoreRow.game_id == box.game_id, BoxScoreRow.universe_id == self.universe_id)
                .one_or_none()
                or BoxScoreRow(game_id=box.game_id, universe_id=self.universe_id)
            )
            row.home_team_id = box.home_team_id
            row.away_team_id = box.away_team_id
            row.home_score = box.home_score
            row.away_score = box.away_score
            row.payload = payload if payload is not None else (box.payload or {})
            row.universe_id = self.universe_id
            session.add(row)
            session.commit()

    def get(self, game_id: str) -> Optional[BoxScore]:
        with self._session_factory() as session:
            row = session.query(BoxScoreRow).filter(BoxScoreRow.game_id == game_id, BoxScoreRow.universe_id == self.universe_id).one_or_none()
            if not row:
                return None
            return BoxScore(
                game_id=row.game_id,
                home_team_id=row.home_team_id,
                away_team_id=row.away_team_id,
                home_score=row.home_score,
                away_score=row.away_score,
                payload=row.payload,
            )
