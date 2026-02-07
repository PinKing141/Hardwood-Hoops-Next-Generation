from typing import Callable, Iterable, Optional

from sqlalchemy.orm import Session

from courthoops.domain.game.events import Event
from courthoops.domain.game.state import GameState
from courthoops.infra.persistence.orm.models import GameRow


class GameRepository:
    """Loads and persists game domain state."""

    def __init__(self, session_factory: Callable[[], Session], universe_id: str = "UNIVERSE"):
        self._session_factory = session_factory
        self.universe_id = universe_id

    def get(self, game_id: str) -> Optional[GameState]:
        with self._session_factory() as session:
            row = session.query(GameRow).filter(GameRow.game_id == game_id, GameRow.universe_id == self.universe_id).one_or_none()
            if not row:
                return None
            return self._to_domain(row)

    def save(self, game_state: GameState) -> None:
        with self._session_factory() as session:
            row = (
                session.query(GameRow)
                .filter(GameRow.game_id == game_state.game_id, GameRow.universe_id == self.universe_id)
                .one_or_none()
                or GameRow(game_id=game_state.game_id, universe_id=self.universe_id)
            )
            row.home_team_id = game_state.home_team_id
            row.away_team_id = game_state.away_team_id
            row.period = game_state.period
            row.clock_seconds = game_state.clock_seconds
            row.score = game_state.score
            row.events = [event.__dict__ for event in game_state.events]
            row.universe_id = self.universe_id
            session.add(row)
            session.commit()

    def append_events(self, game_id: str, events: Iterable[Event]) -> None:
        """Convenience for adding events without reloading the whole game."""
        with self._session_factory() as session:
            row = session.query(GameRow).filter(GameRow.game_id == game_id, GameRow.universe_id == self.universe_id).one_or_none()
            if not row:
                return
            existing = row.events or []
            existing.extend(event.__dict__ for event in events)
            row.events = existing
            session.add(row)
            session.commit()

    @staticmethod
    def _to_domain(row: GameRow) -> GameState:
        game_state = GameState(
            game_id=row.game_id,
            home_team_id=row.home_team_id,
            away_team_id=row.away_team_id,
            period=row.period,
            clock_seconds=row.clock_seconds,
            score=row.score or {"home": 0, "away": 0},
        )
        for payload in row.events or []:
            game_state.record_event(Event(**payload))
        return game_state
