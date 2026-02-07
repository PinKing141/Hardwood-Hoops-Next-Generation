from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import JSON, Boolean, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for SQLAlchemy models."""


class PlayerRow(Base):
    """ORM row for players."""

    __tablename__ = "players"

    universe_id: Mapped[str] = mapped_column(String, default="UNIVERSE", index=True)
    player_id: Mapped[str] = mapped_column("id", String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    class_year: Mapped[str] = mapped_column(String, nullable=False)
    attributes: Mapped[Dict[str, int]] = mapped_column(JSON, default=dict)
    tendencies: Mapped[Dict[str, float]] = mapped_column(JSON, default=dict)
    personality: Mapped[Dict[str, float]] = mapped_column(JSON, default=dict)
    fatigue: Mapped[float] = mapped_column(Float, default=0.0)
    injured: Mapped[bool] = mapped_column(Boolean, default=False)
    injury_days: Mapped[int] = mapped_column(Integer, default=0)
    injury_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    injury_severity: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    injury_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    stats: Mapped[Dict[str, float]] = mapped_column(JSON, default=dict)
    badges: Mapped[List[str]] = mapped_column(JSON, default=list)
    archetype: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class TeamRow(Base):
    """ORM row for teams."""

    __tablename__ = "teams"

    universe_id: Mapped[str] = mapped_column(String, default="UNIVERSE", index=True)
    team_id: Mapped[str] = mapped_column("id", String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    level: Mapped[str] = mapped_column(String, nullable=False)
    region: Mapped[str] = mapped_column(String, nullable=False)
    prestige: Mapped[int] = mapped_column(Integer, default=0)
    coach_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    roster: Mapped[List[str]] = mapped_column(JSON, default=list)
    scholarships: Mapped[int] = mapped_column(Integer, default=0)
    playstyle: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class CoachRow(Base):
    """ORM row for coaches."""

    __tablename__ = "coaches"

    universe_id: Mapped[str] = mapped_column(String, default="UNIVERSE", index=True)
    coach_id: Mapped[str] = mapped_column("id", String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    offensive_iq: Mapped[float] = mapped_column(Float)
    defensive_iq: Mapped[float] = mapped_column(Float)
    development: Mapped[float] = mapped_column(Float)
    substitution: Mapped[float] = mapped_column(Float)
    recruiting: Mapped[float] = mapped_column(Float)
    personality: Mapped[str] = mapped_column(String, default="balanced")


class GameRow(Base):
    """ORM row for games."""

    __tablename__ = "games"

    universe_id: Mapped[str] = mapped_column(String, default="UNIVERSE", index=True)
    game_id: Mapped[str] = mapped_column("id", String, primary_key=True)
    home_team_id: Mapped[str] = mapped_column(String, nullable=False)
    away_team_id: Mapped[str] = mapped_column(String, nullable=False)
    period: Mapped[int] = mapped_column(Integer, default=1)
    clock_seconds: Mapped[int] = mapped_column(Integer, default=20 * 60)
    score: Mapped[Dict[str, int]] = mapped_column(JSON, default=dict)
    events: Mapped[List[dict]] = mapped_column(JSON, default=list)


class BoxScoreRow(Base):
    """ORM row for summarized box score."""

    __tablename__ = "box_scores"

    universe_id: Mapped[str] = mapped_column(String, default="UNIVERSE", index=True)
    game_id: Mapped[str] = mapped_column(String, primary_key=True)
    home_team_id: Mapped[str] = mapped_column(String, nullable=False)
    away_team_id: Mapped[str] = mapped_column(String, nullable=False)
    home_score: Mapped[int] = mapped_column(Integer, default=0)
    away_score: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class PlayByPlayRow(Base):
    """ORM row for play-by-play logs."""

    __tablename__ = "play_by_play"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    universe_id: Mapped[str] = mapped_column(String, default="UNIVERSE", index=True)
    game_id: Mapped[str] = mapped_column(String, index=True)
    event: Mapped[dict] = mapped_column(JSON, default=dict)


class RecruitingRow(Base):
    """ORM row for recruiting records."""

    __tablename__ = "recruiting"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    universe_id: Mapped[str] = mapped_column(String, default="UNIVERSE", index=True)
    player_id: Mapped[str] = mapped_column(String, index=True)
    team_id: Mapped[str] = mapped_column(String, index=True)
    interest: Mapped[float] = mapped_column(Float, default=0.0)
    fit_score: Mapped[float] = mapped_column(Float, default=0.0)
    offer_made: Mapped[bool] = mapped_column(Boolean, default=False)
    committed: Mapped[bool] = mapped_column(Boolean, default=False)
    visits: Mapped[int] = mapped_column(Integer, default=0)
    public_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    true_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    class_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    visit_history: Mapped[List[int]] = mapped_column(JSON, default=list)
    offer_history: Mapped[List[int]] = mapped_column(JSON, default=list)


class PipelineRow(Base):
    """Persists yearly pipeline snapshots (simple JSON blob)."""

    __tablename__ = "pipeline_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    universe_id: Mapped[str] = mapped_column(String, default="UNIVERSE", index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class StandingsRow(Base):
    """Persisted standings snapshot."""

    __tablename__ = "standings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    universe_id: Mapped[str] = mapped_column(String, default="UNIVERSE", index=True)
    season: Mapped[int] = mapped_column(Integer, default=1)
    team_id: Mapped[str] = mapped_column(String, index=True)
    level: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    points_for: Mapped[int] = mapped_column(Integer, default=0)
    points_against: Mapped[int] = mapped_column(Integer, default=0)


class SaveSlotRow(Base):
    """Persisted save slot metadata to link saves to universes/worlds."""

    __tablename__ = "save_slots"

    save_id: Mapped[str] = mapped_column("id", String, primary_key=True)
    universe_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String, default="Save")
    world_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=True)
    last_played_at: Mapped[str] = mapped_column(String, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
