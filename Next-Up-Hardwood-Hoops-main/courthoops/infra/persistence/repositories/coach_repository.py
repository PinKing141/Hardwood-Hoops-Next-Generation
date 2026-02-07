from typing import Callable, Optional

from sqlalchemy.orm import Session

from courthoops.domain.coach.entity import Coach
from courthoops.infra.persistence.orm.models import CoachRow


class CoachRepository:
    """Loads and persists coach domain entities."""

    def __init__(self, session_factory: Callable[[], Session], universe_id: str = "UNIVERSE"):
        self._session_factory = session_factory
        self.universe_id = universe_id

    def get(self, coach_id: str) -> Optional[Coach]:
        with self._session_factory() as session:
            row = session.query(CoachRow).filter(CoachRow.coach_id == coach_id, CoachRow.universe_id == self.universe_id).one_or_none()
            if not row:
                return None
            return self._to_domain(row)

    def save(self, coach: Coach) -> None:
        with self._session_factory() as session:
            row = (
                session.query(CoachRow)
                .filter(CoachRow.coach_id == coach.coach_id, CoachRow.universe_id == self.universe_id)
                .one_or_none()
                or CoachRow(coach_id=coach.coach_id, universe_id=self.universe_id)
            )
            row.name = coach.name
            row.offensive_iq = coach.offensive_iq
            row.defensive_iq = coach.defensive_iq
            row.development = coach.development
            row.substitution = coach.substitution
            row.recruiting = coach.recruiting
            row.personality = coach.personality
            row.universe_id = self.universe_id
            session.add(row)
            session.commit()

    @staticmethod
    def _to_domain(row: CoachRow) -> Coach:
        return Coach(
            coach_id=row.coach_id,
            name=row.name,
            offensive_iq=row.offensive_iq,
            defensive_iq=row.defensive_iq,
            development=row.development,
            substitution=row.substitution,
            recruiting=row.recruiting,
            personality=row.personality,
        )
