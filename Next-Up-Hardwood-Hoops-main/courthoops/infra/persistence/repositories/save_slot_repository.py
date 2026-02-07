from typing import Callable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from courthoops.infra.persistence.orm.models import SaveSlotRow


class SaveSlotRepository:
    """Persists save slots that link a save ID to a universe/world."""

    def __init__(self, session_factory: Callable[[], Session]):
        self._session_factory = session_factory

    def get(self, save_id: str) -> Optional[SaveSlotRow]:
        with self._session_factory() as session:
            return session.get(SaveSlotRow, save_id)

    def list_all(self) -> List[SaveSlotRow]:
        with self._session_factory() as session:
            return session.query(SaveSlotRow).all()

    def upsert(self, save_id: str, *, universe_id: str, name: Optional[str] = None, world_id: Optional[str] = None, metadata: Optional[dict] = None, last_played_at: Optional[str] = None) -> SaveSlotRow:
        with self._session_factory() as session:
            row = session.get(SaveSlotRow, save_id) or SaveSlotRow(save_id=save_id)
            row.universe_id = universe_id
            if name:
                row.name = name
            if world_id:
                row.world_id = world_id
            if metadata is not None:
                row.metadata = metadata
            if last_played_at:
                row.last_played_at = last_played_at
            # keep created_at if existing; otherwise set
            if not row.created_at:
                row.created_at = last_played_at
            session.add(row)
            session.commit()
            return row
