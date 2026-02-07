from typing import Callable, Dict, List

from sqlalchemy.orm import Session

from courthoops.infra.persistence.orm.models import StandingsRow


class StandingsRepository:
    """Persists and retrieves standings snapshots."""

    def __init__(self, session_factory: Callable[[], Session], universe_id: str = "UNIVERSE"):
        self._session_factory = session_factory
        self.universe_id = universe_id

    def save_all(self, standings: Dict[str, dict], level_map: Dict[str, str] | None = None, season: int = 1) -> None:
        with self._session_factory() as session:
            for team_id, rec in standings.items():
                row = StandingsRow(
                    universe_id=self.universe_id,
                    team_id=team_id,
                    season=season,
                    level=(level_map or {}).get(team_id),
                    wins=rec.get("wins", 0),
                    losses=rec.get("losses", 0),
                    points_for=rec.get("points_for", 0),
                    points_against=rec.get("points_against", 0),
                )
                session.add(row)
            session.commit()

    def list_all(self, season: int | None = None) -> List[StandingsRow]:
        with self._session_factory() as session:
            query = session.query(StandingsRow).filter(StandingsRow.universe_id == self.universe_id)
            if season is not None:
                query = query.filter(StandingsRow.season == season)
            return query.all()
