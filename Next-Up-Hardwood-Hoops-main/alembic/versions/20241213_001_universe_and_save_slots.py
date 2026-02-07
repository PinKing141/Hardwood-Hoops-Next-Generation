"""Ensure universe_id columns and save_slots table

Revision ID: 20241213_001
Revises:
Create Date: 2025-12-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "20241213_001"
down_revision = None
branch_labels = None
depends_on = None


UNIVERSE_TABLES = [
    ("players", sa.JSON, sa.JSON),
    ("teams", sa.JSON, sa.JSON),
    ("coaches", sa.JSON, sa.JSON),
    ("games", sa.JSON, sa.JSON),
    ("box_scores", sa.JSON, sa.JSON),
    ("play_by_play", sa.JSON, sa.JSON),
    ("recruiting", sa.JSON, sa.JSON),
    ("pipeline_state", sa.JSON, sa.JSON),
    ("standings", sa.JSON, sa.JSON),
]


def _has_column(bind, table: str, column: str) -> bool:
    inspector = inspect(bind)
    cols = [col["name"] for col in inspector.get_columns(table)]
    return column in cols


def _has_table(bind, table: str) -> bool:
    inspector = inspect(bind)
    return table in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    for table, _, _ in UNIVERSE_TABLES:
        if _has_table(bind, table) and not _has_column(bind, table, "universe_id"):
            op.add_column(table, sa.Column("universe_id", sa.String(), nullable=True, server_default="UNIVERSE"))
    if not _has_table(bind, "save_slots"):
        op.create_table(
            "save_slots",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("universe_id", sa.String(), index=True),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("world_id", sa.String(), nullable=True),
            sa.Column("created_at", sa.String(), nullable=True),
            sa.Column("last_played_at", sa.String(), nullable=True),
            sa.Column("metadata", sa.JSON(), default=dict),
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "save_slots"):
        op.drop_table("save_slots")
    for table, _, _ in UNIVERSE_TABLES:
        if _has_table(bind, table) and _has_column(bind, table, "universe_id"):
            op.drop_column(table, "universe_id")
