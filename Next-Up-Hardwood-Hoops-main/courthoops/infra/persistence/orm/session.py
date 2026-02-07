from typing import Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def make_session_factory(database_url: str, base_metadata=None) -> Callable[[], Session]:
    """Creates a session factory bound to the given database URL."""
    engine = create_engine(database_url, future=True)
    if base_metadata is not None:
        base_metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)
