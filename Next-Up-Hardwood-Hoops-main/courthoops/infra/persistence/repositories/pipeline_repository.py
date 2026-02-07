from typing import Callable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from courthoops.infra.persistence.orm.models import PipelineRow


class PipelineRepository:
    """Persists yearly pipeline state/history."""

    def __init__(self, session_factory: Callable[[], Session], universe_id: str = "UNIVERSE"):
        self._session_factory = session_factory
        self.universe_id = universe_id

    def get_latest(self) -> Optional[dict]:
        with self._session_factory() as session:
            stmt = select(PipelineRow).where(PipelineRow.universe_id == self.universe_id).order_by(PipelineRow.id.desc())
            row = session.scalars(stmt).first()
            return row.payload if row else None

    def save(self, pipeline_state: dict) -> None:
        with self._session_factory() as session:
            row = PipelineRow(payload=pipeline_state, universe_id=self.universe_id)
            session.add(row)
            session.commit()
