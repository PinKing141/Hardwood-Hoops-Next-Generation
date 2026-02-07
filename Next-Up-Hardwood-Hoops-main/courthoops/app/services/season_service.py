from typing import Callable, Dict, Iterable, List, Optional, Tuple

from courthoops.app.use_cases.simulate_game import simulate_game
from courthoops.app.use_cases.start_game import start_game
from courthoops.domain.game.boxscore import BoxScore
from courthoops.domain.game.state import GameState
from courthoops.domain.schedule.game import ScheduleGame
from courthoops.app.services.injury_service import InjuryService
from courthoops.infra.persistence.repositories.boxscore_repository import BoxScoreRepository
from courthoops.infra.persistence.repositories.game_repository import GameRepository
from courthoops.infra.persistence.repositories.playbyplay_repository import PlayByPlayRepository
from courthoops.simulation.engine.game_engine import GameEngine


class SeasonService:
    """
    Simulates a season schedule, persisting game state, play-by-play, and box scores.
    """

    def __init__(
        self,
        game_repo: GameRepository,
        pbp_repo: PlayByPlayRepository,
        boxscore_repo: BoxScoreRepository,
        engine_factory: Callable[[dict], GameEngine],
        injury_service: InjuryService | None = None,
        standings_repo=None,
    ):
        """
        engine_factory: receives context dict with keys:
            - game_state
            - player_lookup
        and returns a configured GameEngine for that matchup.
        """
        self.game_repo = game_repo
        self.pbp_repo = pbp_repo
        self.boxscore_repo = boxscore_repo
        self.engine_factory = engine_factory
        self.injury_service = injury_service or InjuryService()
        self.standings_repo = standings_repo

    def simulate_schedule(
        self,
        schedule: Iterable[Tuple[str, str, str]],  # (game_id, home_team_id, away_team_id) or ScheduleGame
        rosters: Dict[str, List[str]],
        player_lookup: Dict[str, object],
        fatigue_carryover: bool = True,
        injury_recovery: bool = True,
        level_map: Dict[str, str] | None = None,
        pre_game_hook: Optional[Callable[[ScheduleGame, GameState], None]] = None,
        post_game_hook: Optional[Callable[[ScheduleGame, GameState, BoxScore], None]] = None,
        interrupt_on_national_tv: bool = False,
        interrupt_handler: Optional[Callable[[ScheduleGame], object]] = None,
        event_sink: Optional[Callable[[ScheduleGame, object], None]] = None,
    ) -> List[BoxScore]:
        box_scores: List[BoxScore] = []
        # Track fatigue/injuries across games if enabled
        fatigue_state: Dict[str, float] = {}
        injury_state: Dict[str, bool] = {}
        injury_days_state: Dict[str, int] = {}
        derived_level_map: Dict[str, str] = dict(level_map or {})
        for entry in schedule:
            schedule_game = entry if hasattr(entry, "home_team_id") else None
            game_id, home_id, away_id = self._unpack(entry)
            if schedule_game:
                if home_id not in derived_level_map:
                    derived_level_map[home_id] = getattr(schedule_game, "level", None)
                if away_id not in derived_level_map:
                    derived_level_map[away_id] = getattr(schedule_game, "level", None)
            metadata = {}
            if schedule_game:
                metadata = {
                    "level": getattr(schedule_game, "level", None),
                    "phase": getattr(schedule_game, "phase", None),
                    "featured": getattr(schedule_game, "featured", False),
                    "tags": tuple(getattr(schedule_game, "tags", ()) or ()),
                    "national_tv": getattr(schedule_game, "national_tv", False),
                    "postseason_round": getattr(schedule_game, "postseason_round", None),
                }
            game_state = start_game(game_id=game_id, home_team_id=home_id, away_team_id=away_id, rosters=rosters, metadata=metadata)
            if fatigue_carryover:
                for pid, value in fatigue_state.items():
                    game_state.fatigue_by_player[pid] = value
                for pid, hurt in injury_state.items():
                    game_state.injuries[pid] = hurt
                for pid, days in injury_days_state.items():
                    # ensure fouls dict initialized
                    game_state.fouls_by_player.get(pid, 0)
                    if pid in player_lookup:
                        player_lookup[pid].injury_days = days
                        player_lookup[pid].injured = injury_state.get(pid, False)

            if interrupt_on_national_tv and schedule_game and getattr(schedule_game, "national_tv", False):
                action = "pause" if interrupt_handler is None else interrupt_handler(schedule_game)
                # Accept truthy for pause/stop compatibility
                if action in (True, "pause", "stop", "exit"):
                    break
                if action in ("watch", "view", "spectate"):
                    game_state.metadata["watch_mode"] = True
                # any other action continues

            if pre_game_hook and schedule_game:
                pre_game_hook(schedule_game, game_state)

            # Apply pre-game injury roll based on current fatigue/injury proneness
            injuries = self.injury_service.apply_game_injuries(player_lookup.values(), game_state.fatigue_by_player)
            for pid, duration in injuries.items():
                game_state.injuries[pid] = True
                # persist duration on the player objects
                player = player_lookup.get(pid)
                if player:
                    player.injury_days = max(player.injury_days, duration)
                    player.injured = True

            engine = self.engine_factory({"game_state": game_state, "player_lookup": player_lookup})
            watch_mode = bool(game_state.metadata.get("watch_mode"))
            if watch_mode:
                events = []
                for ev in engine.simulate(game_state):
                    events.append(ev)
                    if event_sink and schedule_game:
                        event_sink(schedule_game, ev)
            else:
                events = simulate_game(engine, game_state)
            self.pbp_repo.save_events(game_id, events)
            self.game_repo.save(game_state)
            payload = self._build_boxscore_payload(game_state, events)
            box = BoxScore(
                game_id=game_id,
                home_team_id=home_id,
                away_team_id=away_id,
                home_score=game_state.score["home"],
                away_score=game_state.score["away"],
                payload=payload,
            )
            self.boxscore_repo.save(box)
            box_scores.append(box)
            if post_game_hook and schedule_game:
                post_game_hook(schedule_game, game_state, box)
            if fatigue_carryover:
                fatigue_state.update(game_state.fatigue_by_player)
                injury_state.update(game_state.injuries)
                if injury_recovery:
                    recovered = self.injury_service.apply_season_recovery(player_lookup.values())
                    for pid, did_recover in recovered.items():
                        if did_recover:
                            injury_state[pid] = False
                        injury_days_state[pid] = max(player_lookup[pid].injury_days if pid in player_lookup else 0, 0)
                        # Keep injury flags in sync
                        injury_state[pid] = player_lookup.get(pid, None).injured if pid in player_lookup else injury_state.get(pid, False)

        # Persist standings snapshot if desired
        if self.standings_repo:
            standings = compute_standings(box_scores)
            # no level map available here; caller can pass or repo can ignore
            self.standings_repo.save_all(standings, level_map=derived_level_map)
        return box_scores

    def _build_boxscore_payload(self, game_state, events) -> dict:
        player_team = {}
        for team_id, roster in game_state.rosters.items():
            for pid in roster:
                player_team[pid] = team_id

        players = {
            pid: {
                "team_id": team_id,
                "points": 0,
                "fgm": 0,
                "fga": 0,
                "rebounds": 0,
                "assists": 0,
                "steals": 0,
                "blocks": 0,
                "turnovers": 0,
                "fouls": 0,
                "three_m": 0,
                "three_a": 0,
            }
            for pid, team_id in player_team.items()
        }
        teams = {game_state.home_team_id: {"points": 0}, game_state.away_team_id: {"points": 0}}

        for event in events:
            payload = getattr(event, "payload", {}) or {}
            team_id = payload.get("team_id")
            pid = payload.get("player_id")
            if event.event_type == "shot_made":
                pts = payload.get("points", 0)
                is_three = payload.get("is_three", False)
                if team_id in teams:
                    teams[team_id]["points"] = teams[team_id].get("points", 0) + pts
                if pid in players:
                    players[pid]["points"] += pts
                    players[pid]["fgm"] += 1
                    players[pid]["fga"] += 1
                    if is_three:
                        players[pid]["three_m"] += 1
                        players[pid]["three_a"] += 1
                assist_pid = payload.get("assist_player_id")
                if assist_pid and assist_pid in players:
                    players[assist_pid]["assists"] += 1
                # Free throws: approximate 1 point shot_made that is not a three and flagged as FT
                if payload.get("is_free_throw", False) and pid in players:
                    players[pid]["ftm"] = players[pid].get("ftm", 0) + 1
                    players[pid]["fta"] = players[pid].get("fta", 0) + 1
            elif event.event_type == "shot_missed":
                if pid in players:
                    players[pid]["fga"] += 1
                    if payload.get("is_three", False):
                        players[pid]["three_a"] += 1
                    if payload.get("is_free_throw", False):
                        players[pid]["fta"] = players[pid].get("fta", 0) + 1
            elif event.event_type == "rebound":
                if pid in players:
                    players[pid]["rebounds"] += 1
            elif event.event_type == "foul":
                if pid in players:
                    players[pid]["fouls"] += 1
                # Track team fouls if needed later
            elif event.event_type == "turnover":
                if pid in players:
                    players[pid]["turnovers"] += 1
            elif event.event_type == "steal":
                if pid in players:
                    players[pid]["steals"] += 1
            elif event.event_type == "block":
                if pid in players:
                    players[pid]["blocks"] += 1

        # Track minutes played from game state
        for pid, minutes in getattr(game_state, "minutes_played", {}).items():
            if pid in players:
                players[pid]["minutes"] = round(minutes, 1)

        # Compute team totals for advanced metrics
        team_totals: Dict[str, dict] = {
            tid: {"fga": 0, "fgm": 0, "turnovers": 0, "minutes": 0.0, "fta": 0, "ftm": 0}
            for tid in teams.keys()
        }
        for pid, line in players.items():
            tid = line["team_id"]
            if tid in team_totals:
                team_totals[tid]["fga"] += line["fga"]
                team_totals[tid]["fgm"] += line["fgm"]
                team_totals[tid]["turnovers"] += line["turnovers"]
                team_totals[tid]["minutes"] += line.get("minutes", 0.0)
                team_totals[tid]["fta"] += line.get("fta", 0)
                team_totals[tid]["ftm"] += line.get("ftm", 0)

        # Advanced: TS% (with FT proxy), AST%, usage proxy, ORtg/DRtg estimates
        for pid, line in players.items():
            tid = line["team_id"]
            totals = team_totals.get(tid, {"fga": 0, "fgm": 0, "turnovers": 0, "minutes": 0.0, "fta": 0, "ftm": 0})
            fga = line["fga"]
            fta = line.get("fta", 0)
            ftm = line.get("ftm", 0)
            pts = line["points"]
            turnovers = line["turnovers"]
            team_actions = max(1, totals["fga"] + 0.44 * totals["fta"] + totals["turnovers"])
            # True shooting with FT proxy
            ts = pts / (2 * max(1, fga + 0.44 * fta)) if (fga + fta) > 0 else 0.0
            ast_pct = line["assists"] / max(1, totals["fgm"]) if totals["fgm"] > 0 else 0.0
            usage = (fga + 0.44 * fta + turnovers) / team_actions
            # Simple offensive rating estimate: points per 100 possessions used
            possessions_used = fga + 0.44 * fta + turnovers
            ortg = (pts / max(possessions_used, 1)) * 100
            # Team defensive rating proxy: opponent points per 100 possessions
            # (requires we have both teams' points; use box scores totals)
            drtg = None
            if tid == game_state.home_team_id:
                opp_id, opp_pts = game_state.away_team_id, game_state.score.get("away", 0)
            else:
                opp_id, opp_pts = game_state.home_team_id, game_state.score.get("home", 0)
            opp_totals = team_totals.get(opp_id, {"fga": 0, "fta": 0, "turnovers": 0})
            team_possessions = totals["fga"] + 0.44 * totals["fta"] + totals["turnovers"]
            opp_possessions = opp_totals["fga"] + 0.44 * opp_totals["fta"] + opp_totals["turnovers"]
            est_possessions = max(1, (team_possessions + opp_possessions) / 2)
            drtg = (opp_pts / est_possessions) * 100
            line["ts_pct"] = round(ts, 3)
            line["ast_pct"] = round(ast_pct, 3)
            line["usage"] = round(usage, 3)
            line["ortg"] = round(ortg, 1)
            line["drtg"] = round(drtg, 1) if drtg is not None else None

        return {"players": players, "teams": teams}

    @staticmethod
    def _unpack(entry):
        if hasattr(entry, "home_team_id"):
            return entry.game_id, entry.home_team_id, entry.away_team_id
        return entry


def compute_standings(box_scores: List[BoxScore]) -> Dict[str, dict]:
    """Aggregate wins/losses and points for/against from box scores."""
    table: Dict[str, dict] = {}
    for box in box_scores:
        for team_id, score, opp_score in (
            (box.home_team_id, box.home_score, box.away_score),
            (box.away_team_id, box.away_score, box.home_score),
        ):
            entry = table.setdefault(team_id, {"wins": 0, "losses": 0, "points_for": 0, "points_against": 0})
            entry["points_for"] += score
            entry["points_against"] += opp_score
            if score > opp_score:
                entry["wins"] += 1
            else:
                entry["losses"] += 1
    return table


def aggregate_player_season_stats(box_scores: List[BoxScore]) -> Dict[str, dict]:
    """Aggregate per-player season totals from box score payloads."""
    totals: Dict[str, dict] = {}
    for box in box_scores:
        payload = box.payload or {}
        players = payload.get("players", {})
        for pid, line in players.items():
            entry = totals.setdefault(
                pid,
                {
                    "games": 0,
                    "points": 0,
                    "fgm": 0,
                    "fga": 0,
                    "three_m": 0,
                    "three_a": 0,
                    "rebounds": 0,
                    "assists": 0,
                    "steals": 0,
                    "blocks": 0,
                    "turnovers": 0,
                    "fouls": 0,
                },
            )
            entry["games"] += 1
            for key in ("points", "fgm", "fga", "three_m", "three_a", "rebounds", "assists", "steals", "blocks", "turnovers", "fouls"):
                entry[key] += line.get(key, 0)
    return totals
