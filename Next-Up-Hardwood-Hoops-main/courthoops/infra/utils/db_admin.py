import os
import sqlite3
from typing import Iterable


UNIVERSE_TABLES = [
    "players",
    "teams",
    "coaches",
    "games",
    "box_scores",
    "play_by_play",
    "recruiting",
    "pipeline_state",
    "standings",
]


def _column_exists(cur: sqlite3.Cursor, table: str, column: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    return column in cols


def _ensure_column(cur: sqlite3.Cursor, table: str, column: str, ddl: str) -> None:
    if not _column_exists(cur, table, column):
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def _ensure_table(cur: sqlite3.Cursor, table: str, ddl: str) -> None:
    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if not cur.fetchone():
        cur.execute(ddl)


def migrate_sqlite_universe_columns(sqlite_path: str) -> None:
    """
    Adds universe_id columns to existing SQLite tables and creates save_slots if missing.
    Safe to run multiple times.
    """
    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"SQLite DB not found at {sqlite_path}")

    con = sqlite3.connect(sqlite_path)
    cur = con.cursor()

    for table in UNIVERSE_TABLES:
        try:
            _ensure_column(cur, table, "universe_id", "TEXT DEFAULT 'UNIVERSE'")
        except sqlite3.OperationalError:
            # Table might not exist yet; skip silently
            continue

    _ensure_table(
        cur,
        "save_slots",
        """
        CREATE TABLE save_slots (
            id TEXT PRIMARY KEY,
            universe_id TEXT,
            name TEXT,
            world_id TEXT,
            created_at TEXT,
            last_played_at TEXT,
            metadata JSON
        );
        """,
    )

    con.commit()
    con.close()


def sqlite_path_from_url(database_url: str) -> str:
    """Extracts the file path from a sqlite:/// URL."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Only sqlite:/// URLs are supported for migration.")
    return database_url.replace(prefix, "", 1)
