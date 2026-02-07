class PlayerRepository:
    """Loads and persists player domain entities."""

    def get(self, player_id: str):
        raise NotImplementedError

    def save(self, player):
        raise NotImplementedError

from typing import Callable, Iterable, Optional

from sqlalchemy.orm import Session

from courthoops.domain.player.entity import (
    Player,
    PlayerAttributes,
    PlayerPersonality,
    PlayerTendencies,
)
from courthoops.infra.persistence.orm.models import PlayerRow


class PlayerRepository:
    """Loads and persists player domain entities."""

    def __init__(self, session_factory: Callable[[], Session], universe_id: str = "UNIVERSE"):
        self._session_factory = session_factory
        self.universe_id = universe_id

    def get(self, player_id: str) -> Optional[Player]:
        with self._session_factory() as session:
            row = session.query(PlayerRow).filter(PlayerRow.player_id == player_id, PlayerRow.universe_id == self.universe_id).one_or_none()
            if not row:
                return None
            return self._to_domain(row)

    def save(self, player: Player) -> None:
        with self._session_factory() as session:
            row = (
                session.query(PlayerRow)
                .filter(PlayerRow.player_id == player.player_id, PlayerRow.universe_id == self.universe_id)
                .one_or_none()
                or PlayerRow(player_id=player.player_id, universe_id=self.universe_id)
            )
            row.name = player.name
            row.class_year = player.class_year
            row.attributes = player.attributes.__dict__
            row.tendencies = {
                "shot_selection": player.tendencies.shot_selection,
                "aggression": player.tendencies.aggression,
                "shot_profile": player.tendencies.shot_profile,
                "rim_aggression": player.tendencies.rim_aggression,
                "shot_creation": player.tendencies.shot_creation,
                "playmaking_bias": player.tendencies.playmaking_bias,
                "pass_profile": player.tendencies.pass_profile,
                "defensive_style": player.tendencies.defensive_style,
                "help_defense": player.tendencies.help_defense,
                "rebound_bias": player.tendencies.rebound_bias,
                "athletic_usage": player.tendencies.athletic_usage,
            }
            row.personality = {
                "work_ethic": player.personality.work_ethic,
                "coachability": player.personality.coachability,
                "competitiveness": player.personality.competitiveness,
            }
            row.fatigue = player.fatigue
            row.injured = player.injured
            row.injury_days = player.injury_days
            row.injury_type = getattr(player, "injury_type", None)
            row.injury_severity = getattr(player, "injury_severity", None)
            row.injury_status = player.injury_status or (player.stats.get("injury_status") if isinstance(player.stats, dict) else None)
            stats = dict(player.stats) if isinstance(player.stats, dict) else {}
            stats["minutes_allocation"] = player.minutes_allocation
            if player.injury_status:
                stats["injury_status"] = player.injury_status
            row.stats = stats
            row.badges = player.badges
            row.archetype = player.archetype
            row.universe_id = self.universe_id
            session.add(row)
            session.commit()

    def list_all(self) -> list[Player]:
        with self._session_factory() as session:
            rows = session.query(PlayerRow).filter(PlayerRow.universe_id == self.universe_id).all()
            return [self._to_domain(row) for row in rows]

    def list_by_ids(self, player_ids: Iterable[str]) -> list[Player]:
        ids = list(player_ids)
        if not ids:
            return []
        with self._session_factory() as session:
            rows = session.query(PlayerRow).filter(PlayerRow.universe_id == self.universe_id, PlayerRow.player_id.in_(ids)).all()
            return [self._to_domain(row) for row in rows]

    def list_by_class_year(self, class_year: str) -> list[Player]:
        with self._session_factory() as session:
            rows = session.query(PlayerRow).filter(PlayerRow.universe_id == self.universe_id, PlayerRow.class_year == class_year).all()
            return [self._to_domain(row) for row in rows]

    def list_by_team_level(self, level: str, team_repo) -> list[Player]:
        """
        List players whose teams are in a given level (requires team_repo to resolve teams/rosters).
        TeamRepo must expose list_by_level returning Team entities with roster ids populated.
        """
        teams = team_repo.list_by_level(level)
        player_ids = {pid for team in teams for pid in getattr(team, "roster", [])}
        return [p for p in self.list_all() if p.player_id in player_ids]

    @staticmethod
    def _to_domain(row: PlayerRow) -> Player:
        attr_data = row.attributes or {}
        tend_data = row.tendencies or {}
        return Player(
            player_id=row.player_id,
            name=row.name,
            class_year=row.class_year,
            attributes=PlayerAttributes(
                layup=attr_data.get("layup", 50),
                dunk=attr_data.get("dunk", 50),
                inside=attr_data.get("inside", 50),
                mid_range=attr_data.get("mid_range", 50),
                three_point=attr_data.get("three_point", 50),
                free_throw=attr_data.get("free_throw", 50),
                offensive_rebound=attr_data.get("offensive_rebound", 50),
                ball_control=attr_data.get("ball_control", 50),
                passing=attr_data.get("passing", 50),
                defensive_rebound=attr_data.get("defensive_rebound", 50),
                perimeter_defense=attr_data.get("perimeter_defense", 50),
                interior_defense=attr_data.get("interior_defense", 50),
                steal=attr_data.get("steal", 50),
                block=attr_data.get("block", 50),
                speed=attr_data.get("speed", 50),
                agility=attr_data.get("agility", 50),
                vertical=attr_data.get("vertical", 50),
                strength=attr_data.get("strength", 50),
                stamina=attr_data.get("stamina", 50),
                offensive_iq=attr_data.get("offensive_iq", 50),
                defensive_iq=attr_data.get("defensive_iq", 50),
                hustle=attr_data.get("hustle", 50),
                potential=attr_data.get("potential", 50),
                injury_proneness=attr_data.get("injury_proneness", 50),
                clutch=attr_data.get("clutch", 50),
                consistency=attr_data.get("consistency", 50),
                decision_discipline=attr_data.get("decision_discipline", 50),
            ),
            tendencies=PlayerTendencies(
                shot_selection=tend_data.get("shot_selection", 0.5),
                aggression=tend_data.get("aggression", 0.5),
                shot_profile=tend_data.get("shot_profile", [0.4, 0.25, 0.35]),
                rim_aggression=tend_data.get("rim_aggression", [0.6, 0.4]),
                shot_creation=tend_data.get("shot_creation", [0.4, 0.25, 0.35]),
                playmaking_bias=tend_data.get("playmaking_bias", [0.4, 0.35, 0.25]),
                pass_profile=tend_data.get("pass_profile", [0.4, 0.25, 0.35]),
                defensive_style=tend_data.get("defensive_style", [0.45, 0.35, 0.20]),
                help_defense=tend_data.get("help_defense", [0.35, 0.35, 0.30]),
                rebound_bias=tend_data.get("rebound_bias", [0.4, 0.2, 0.4]),
                athletic_usage=tend_data.get("athletic_usage", [0.3, 0.25, 0.25, 0.2]),
            ),
            personality=PlayerPersonality(
                work_ethic=row.personality.get("work_ethic", 0.5),
                coachability=row.personality.get("coachability", 0.5),
                competitiveness=row.personality.get("competitiveness", 0.5),
            ),
            fatigue=row.fatigue,
            injured=row.injured,
            stats=row.stats,
            badges=row.badges,
            archetype=row.archetype,
            minutes_allocation=row.stats.get("minutes_allocation", 20.0) if isinstance(row.stats, dict) else 20.0,
            injury_days=getattr(row, "injury_days", 0),
            injury_type=getattr(row, "injury_type", None),
            injury_severity=getattr(row, "injury_severity", None),
            injury_status=getattr(row, "injury_status", None),
        )
