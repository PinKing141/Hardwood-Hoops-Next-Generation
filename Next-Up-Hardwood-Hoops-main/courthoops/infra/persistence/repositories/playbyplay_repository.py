from typing import Callable, Iterable

from sqlalchemy.orm import Session

from courthoops.domain.game.events import Event
from courthoops.infra.persistence.orm.models import PlayByPlayRow


class PlayByPlayRepository:
    """Persists play-by-play events."""

    def __init__(self, session_factory: Callable[[], Session], universe_id: str = "UNIVERSE"):
        self._session_factory = session_factory
        self.universe_id = universe_id

    def save_events(self, game_id: str, events: Iterable[Event]) -> None:
        """Stores each event as a row for querying/replays."""
        with self._session_factory() as session:
            for event in events:
                session.add(PlayByPlayRow(game_id=game_id, universe_id=self.universe_id, event=event.__dict__))
            session.commit()
