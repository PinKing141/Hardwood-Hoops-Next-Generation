from typing import Callable, Optional

from sqlalchemy.orm import Session

from courthoops.domain.team.entity import Team
from courthoops.infra.persistence.orm.models import TeamRow


class TeamRepository:
    """Loads and persists team domain entities."""

    def __init__(self, session_factory: Callable[[], Session], universe_id: str = "UNIVERSE"):
        self._session_factory = session_factory
        self.universe_id = universe_id

    def get(self, team_id: str) -> Optional[Team]:
        with self._session_factory() as session:
            row = session.query(TeamRow).filter(TeamRow.team_id == team_id, TeamRow.universe_id == self.universe_id).one_or_none()
            if not row:
                return None
            return self._to_domain(row)

    def save(self, team: Team) -> None:
        with self._session_factory() as session:
            row = (
                session.query(TeamRow)
                .filter(TeamRow.team_id == team.team_id, TeamRow.universe_id == self.universe_id)
                .one_or_none()
                or TeamRow(team_id=team.team_id, universe_id=self.universe_id)
            )
            row.name = team.name
            row.level = team.level
            row.region = team.region
            row.prestige = team.prestige
            row.coach_id = team.coach_id
            row.roster = list(team.roster)
            row.scholarships = team.scholarships
            row.playstyle = team.playstyle
            row.universe_id = self.universe_id
            session.add(row)
            session.commit()

    def list_all(self) -> list[Team]:
        with self._session_factory() as session:
            rows = session.query(TeamRow).filter(TeamRow.universe_id == self.universe_id).all()
            return [self._to_domain(row) for row in rows]

    def list_by_level(self, level: str) -> list[Team]:
        with self._session_factory() as session:
            rows = session.query(TeamRow).filter(TeamRow.universe_id == self.universe_id, TeamRow.level == level).all()
            return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: TeamRow) -> Team:
        return Team(
            team_id=row.team_id,
            name=row.name,
            level=row.level,
            region=row.region,
            prestige=row.prestige,
            coach_id=row.coach_id,
            roster=row.roster,
            scholarships=row.scholarships,
            playstyle=row.playstyle,
        )
