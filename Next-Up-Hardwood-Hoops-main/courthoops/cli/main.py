import argparse
import threading
from datetime import datetime
from queue import Queue

from courthoops.app.use_cases.simulate_game import simulate_game
from courthoops.app.use_cases.start_game import start_game
from courthoops.app.services.scouting_service import ScoutingService
from courthoops.app.services.injury_service import InjuryService
from courthoops.infra.generators.world_generator import WorldGenerator
from courthoops.infra.generators.schedule_generator import ScheduleGenerator
from courthoops.infra.persistence.orm.models import Base
from courthoops.infra.persistence.orm.session import make_session_factory
from courthoops.infra.persistence.repositories.coach_repository import CoachRepository
from courthoops.infra.persistence.repositories.game_repository import GameRepository
from courthoops.infra.persistence.repositories.player_repository import PlayerRepository
from courthoops.infra.persistence.repositories.playbyplay_repository import PlayByPlayRepository
from courthoops.infra.persistence.repositories.boxscore_repository import BoxScoreRepository
from courthoops.infra.persistence.repositories.recruiting_repository import RecruitingRepository
from courthoops.infra.persistence.repositories.save_slot_repository import SaveSlotRepository
from courthoops.infra.persistence.repositories.team_repository import TeamRepository
from courthoops.infra.persistence.repositories.standings_repository import StandingsRepository
from courthoops.infra.utils.config import AppConfig
from courthoops.infra.utils.logger import get_logger
from courthoops.infra.utils.rng import PythonRNG
from courthoops.ui.flavor_copy import pre_game_lines, post_game_lines, schedule_line
from courthoops.simulation.engine.foul_engine import FoulEngine
from courthoops.simulation.engine.game_engine import GameEngine
from courthoops.simulation.engine.possession_engine import PossessionEngine
from courthoops.simulation.engine.rebound_engine import ReboundEngine
from courthoops.simulation.engine.shot_engine import ShotEngine
from courthoops.simulation.engine.substitution_engine import SubstitutionEngine
from courthoops.simulation.engine.team_strength import TeamStrengthService
from courthoops.app.services.season_service import SeasonService, compute_standings, aggregate_player_season_stats
from courthoops.app.services.progression_service import ProgressionService
from courthoops.simulation.playbyplay.text_renderer import TextRenderer
from courthoops.ui.textual.watch_screen import WatchModeApp
from courthoops.infra.utils.db_admin import migrate_sqlite_universe_columns, sqlite_path_from_url


def main() -> None:
    parser = argparse.ArgumentParser(description="Courthoops CLI")
    parser.add_argument("--demo", action="store_true", help="Run a tiny demo game simulation.")
    parser.add_argument("--show-boxes", action="store_true", help="After sim, print box score summaries.")
    parser.add_argument("--show-injuries", action="store_true", help="After sim, print injury report.")
    parser.add_argument("--show-scouting", action="store_true", help="Print top scouting reports (public OVR/build/roles).")
    parser.add_argument("--show-flavor-hooks", action="store_true", help="Log pre/post-game flavor copy for UI surfaces.")
    parser.add_argument("--show-schedule", action="store_true", help="Print schedule with featured/background/TV tags before sim.")
    parser.add_argument("--interrupt-national-tv", action="store_true", help="Pause season sim when encountering national TV slots.")
    parser.add_argument("--watch-ui", action="store_true", help="Open Textual watch-mode viewer when choosing to watch a game.")
    parser.add_argument("--world-id", type=str, help="Optional world identifier to namespace generated teams/players/coaches.")
    parser.add_argument("--skip-bootstrap-if-data", action="store_true", help="Do not regenerate a world if players already exist in the DB.")
    parser.add_argument("--db-path", type=str, help="Override database path (e.g., ./my_universe.db).")
    parser.add_argument("--universe-id", type=str, help="Optional universe identifier for multi-universe persistence.")
    parser.add_argument("--save-id", type=str, help="Save slot identifier; loads the matching universe.")
    parser.add_argument("--save-name", type=str, help="Human-readable save name for new slots.")
    parser.add_argument("--migrate-db", action="store_true", help="Add universe_id columns and save_slots table to an existing SQLite DB, then exit.")
    parser.add_argument("--list-saves", action="store_true", help="List save slots (id, universe, world, timestamps) and exit.")
    parser.add_argument("--show-standings", action="store_true", help="Print standings after season sim.")
    parser.add_argument("--show-prospects", action="store_true", help="Print recruiting prospect board (public view).")
    parser.add_argument("--show-prospects-ai", action="store_true", help="Print AI-facing prospect board (true ratings).")
    parser.add_argument("--prospects-class", type=int, help="Filter prospect board by class rank ceiling (<=).")
    parser.add_argument("--prospects-region", type=str, help="Filter prospect board by region match.")
    parser.add_argument("--prospects-interest-min", type=float, help="Filter prospect board by minimum interest (0-1).")
    parser.add_argument("--prospects-interest-max", type=float, help="Filter prospect board by maximum interest (0-1).")
    parser.add_argument("--no-postseason", action="store_true", help="Skip postseason bracket generation.")
    parser.add_argument("--no-standings", action="store_true", help="Do not persist standings snapshot.")
    args = parser.parse_args()

    config = AppConfig()
    if args.db_path:
        db_url = args.db_path
        if "://" not in db_url:
            db_url = f"sqlite:///{db_url}"
        config.database_url = db_url
    if args.universe_id:
        config.universe_id = args.universe_id.upper()
    logger = get_logger("courthoops-cli")
    session_factory = make_session_factory(config.database_url, Base.metadata)
    save_repo = SaveSlotRepository(session_factory)

    if args.migrate_db:
        try:
            sqlite_path = sqlite_path_from_url(config.database_url)
            migrate_sqlite_universe_columns(sqlite_path)
            logger.info("Migration complete for %s", sqlite_path)
        except Exception as e:
            logger.error("Migration failed: %s", e)
        return

    # If save slot provided, adopt its universe_id so we load the right world.
    if args.save_id:
        slot = save_repo.get(args.save_id)
        if slot:
            config.universe_id = slot.universe_id
            logger.info("Loaded save slot %s (universe %s)", args.save_id, slot.universe_id)
        else:
            logger.info("Save slot %s not found; will create it.", args.save_id)

    if args.list_saves:
        slots = save_repo.list_all()
        if not slots:
            logger.info("No save slots found.")
        else:
            for slot in slots:
                logger.info(
                    "Save %s | universe=%s | world=%s | created=%s | last_played=%s | name=%s",
                    slot.save_id,
                    slot.universe_id,
                    slot.world_id,
                    slot.created_at,
                    slot.last_played_at,
                    slot.name,
                )
        return

    universe_id = config.universe_id.upper()
    player_repo = PlayerRepository(session_factory, universe_id=universe_id)
    team_repo = TeamRepository(session_factory, universe_id=universe_id)
    coach_repo = CoachRepository(session_factory, universe_id=universe_id)
    game_repo = GameRepository(session_factory, universe_id=universe_id)
    playbyplay_repo = PlayByPlayRepository(session_factory, universe_id=universe_id)
    boxscore_repo = BoxScoreRepository(session_factory, universe_id=universe_id)
    recruiting_repo = RecruitingRepository(session_factory, universe_id=universe_id)
    standings_repo = None if getattr(args, "no_standings", False) else StandingsRepository(session_factory, universe_id=universe_id)

    rng = PythonRNG(seed=config.rng_seed)
    from courthoops.infra.generators.city_service import CityService

    world_id = (args.world_id or datetime.now().strftime("W%Y%m%d%H%M%S")).upper()
    save_id = (args.save_id or world_id).upper()
    city_service = CityService(config.city_db_path, rng)
    world_generator = WorldGenerator(
        player_repo,
        team_repo,
        coach_repo,
        rng,
        city_service=city_service,
        hs_team_count=6,
        aau_team_count=4,
        hs_roster_size=9,
        aau_roster_size=9,
        hs_prestige_top=62,
        hs_prestige_floor=42,
        aau_prestige_top=72,
        aau_prestige_floor=55,
        hs_region_bias={"East": 0.3, "South": 0.25, "Midwest": 0.25, "West": 0.2},
        aau_region_bias={"East": 0.25, "South": 0.3, "Midwest": 0.25, "West": 0.2},
        world_id=world_id,
        universe_id=universe_id,
    )
    schedule_generator = ScheduleGenerator()
    scouting_service = ScoutingService()
    injury_service = InjuryService()
    progression_service = ProgressionService(
        max_growth=config.progression_max_growth,
        decline_start_age=config.progression_decline_start_age,
        decline_rate=config.progression_decline_rate,
    )
    watch_queue = Queue() if args.watch_ui else None
    watch_thread = None
    if watch_queue:
        def _run_watch():
            app = WatchModeApp(watch_queue, title="Watch Mode PBP")
            app.run()
        watch_thread = threading.Thread(target=_run_watch, daemon=True)
        watch_thread.start()

    if args.demo:
        existing_players = player_repo.list_all()
        if args.skip_bootstrap_if_data and existing_players:
            logger.info("Skipping bootstrap; %s players already in DB for universe %s. Using persisted world.", len(existing_players), universe_id)
        else:
            logger.info("Bootstrapping demo world with world_id=%s (universe %s)...", world_id, universe_id)
            world_generator.bootstrap_world()
            existing_players = player_repo.list_all()
        # Ensure save slot exists and is updated
        save_repo.upsert(
            save_id,
            universe_id=universe_id,
            name=args.save_name or save_id,
            world_id=world_id,
            metadata={"generated": True},
            last_played_at=datetime.now().isoformat(),
        )

        teams = team_repo.list_all()
        rosters = {team.team_id: team.roster for team in teams}
        players = existing_players or player_repo.list_all()
        player_lookup = {p.player_id: p for p in players}
        # Position map from player stats if present; fallback heuristic
        position_map = {}
        for p in players:
            pos = (p.stats or {}).get("position") if hasattr(p, "stats") else None
            if pos:
                position_map[p.player_id] = pos
        if not position_map:
            for team in teams:
                for idx, pid in enumerate(team.roster):
                    if idx < 2:
                        position_map[pid] = "PG"
                    elif idx < 4:
                        position_map[pid] = "SF"
                    else:
                        position_map[pid] = "C"

        team_ids = list(rosters.keys())
        home_id = team_ids[0] if team_ids else "HOME"
        away_id = team_ids[1] if len(team_ids) > 1 else (team_ids[0] if team_ids else "AWAY")
        dummy_state = start_game(game_id="DEMO", home_team_id=home_id, away_team_id=away_id, rosters=rosters)
        strength = TeamStrengthService(dummy_state, player_lookup)

        def engine_factory(context):
            gs = context["game_state"]
            strength_service = TeamStrengthService(gs, player_lookup)
            shot_engine = ShotEngine(
                rng=rng,
                offense_strength_fn=strength_service.offense_strength,
                defense_strength_fn=strength_service.defense_strength,
                player_lookup=player_lookup,
            )
            rebound_engine = ReboundEngine(
                rng=rng,
                offense_strength_fn=strength_service.offense_strength,
                defense_strength_fn=strength_service.defense_strength,
                player_lookup=player_lookup,
            )
            foul_engine = FoulEngine(
                rng=rng,
                offense_strength_fn=strength_service.offense_strength,
                defense_strength_fn=strength_service.defense_strength,
                player_lookup=player_lookup,
            )
            sub_engine = SubstitutionEngine(player_lookup=player_lookup)
            possession_engine = PossessionEngine(shot_engine, rebound_engine, foul_engine, player_lookup=player_lookup)
            return GameEngine(possession_engine, sub_engine)

        def log_pre(schedule_game, game_state):
            for line in pre_game_lines(schedule_game):
                logger.info("[PRE][%s] %s", schedule_game.game_id, line)

        def log_post(schedule_game, game_state, box_score):
            for line in post_game_lines(schedule_game, box_score):
                logger.info("[POST][%s] %s", schedule_game.game_id, line)

        text_renderer = TextRenderer()

        def stream_event(schedule_game, event):
            line = text_renderer.render(event)
            if watch_queue:
                watch_queue.put(line)
            logger.info("[PBP][%s] %s", schedule_game.game_id, line)

        # Single demo season using exposure-driven HS/AAU pacing
        season_service = SeasonService(game_repo, playbyplay_repo, boxscore_repo, engine_factory, injury_service=injury_service, standings_repo=standings_repo)
        hs_teams = [t.team_id for t in teams if t.level == "HS"] or [t.team_id for t in teams if t.level == "D1"]
        aau_teams = [t.team_id for t in teams if t.level == "AAU"] or hs_teams
        career_schedule = schedule_generator.generate_exposure_career_schedule(hs_teams, aau_teams, rng=rng)

        def tv_interrupt_handler(schedule_game):
            prompt = (
                f"National TV: {schedule_game.home_team_id} vs {schedule_game.away_team_id} "
                f"(week {schedule_game.week}, {schedule_game.phase or schedule_game.level}) "
                "[w]atch/[s]im/[p]ause? "
            )
            try:
                choice = input(prompt).strip().lower()
            except Exception:
                choice = "sim"
            if choice.startswith("p"):
                logger.info("Pausing sim at %s", schedule_game.game_id)
                return "pause"
            if choice.startswith("w"):
                logger.info("Switching to watch-mode sim for %s", schedule_game.game_id)
                return "watch"
            logger.info("Continuing sim for %s", schedule_game.game_id)
            return "sim"

        if args.show_schedule:
            for g in career_schedule:
                logger.info("SCHED %s", schedule_line(g))

        level_map = {t.team_id: t.level for t in teams}
        box_scores = season_service.simulate_schedule(
            career_schedule,
            rosters,
            player_lookup,
            level_map=level_map,
            pre_game_hook=log_pre if args.show_flavor_hooks else None,
            post_game_hook=log_post if args.show_flavor_hooks else None,
            interrupt_on_national_tv=args.interrupt_national_tv,
            interrupt_handler=tv_interrupt_handler if args.interrupt_national_tv else None,
            event_sink=stream_event,
        )
        standings_regular = compute_standings(box_scores)

        if not getattr(args, "no_postseason", False):
            logger.info("Postseason flag ignored: career schedule already includes playoff rounds.")

        if args.show_scouting:
            rec_map = {r.player_id: r for r in recruiting_repo.list_all()}
            reports = scouting_service.scouting_reports(players, recruiting=rec_map, position_map=position_map)
            top = sorted(reports.items(), key=lambda kv: kv[1]["public_ovr"], reverse=True)[:10]
            for pid, rep in top:
                logger.info(
                    "Scouting: %s | OVR %.1f | %s | Roles: %s | Status: %s | ClassRank:%s PublicRating:%s Visits:%s Offers:%s",
                    pid,
                    rep["public_ovr"],
                    rep["build_name"],
                    ", ".join(rep["role_descriptors"]),
                    rep.get("status", "healthy"),
                    rep.get("class_rank"),
                    rep.get("public_rating"),
                    rep.get("visits"),
                    rep.get("offers"),
                )

        if args.show_prospects:
            prospects = recruiting_repo.list_all()
            if args.prospects_class:
                prospects = [p for p in prospects if p.class_rank and p.class_rank <= args.prospects_class]
            if args.prospects_region:
                prospects = [p for p in prospects if (p.region or "").lower() == args.prospects_region.lower()]
            if args.prospects_interest_min is not None:
                prospects = [p for p in prospects if p.interest >= args.prospects_interest_min]
            if args.prospects_interest_max is not None:
                prospects = [p for p in prospects if p.interest <= args.prospects_interest_max]
            # Public board sorted by public_rating/class_rank
            board = sorted(prospects, key=lambda r: ((r.public_rating or 0), -(r.class_rank or 9999)), reverse=True)[:15]
            for rec in board:
                logger.info(
                    "Prospect: %s | Team:%s Public:%.1f Rank:%s Region:%s Interest:%.2f Visits:%s Offers:%s",
                    rec.player_id,
                    rec.team_id,
                    rec.public_rating or 0.0,
                    rec.class_rank,
                    rec.region,
                    rec.interest,
                    rec.visit_history,
                    rec.offer_history,
                )

        if args.show_prospects_ai:
            prospects = recruiting_repo.list_all()
            if args.prospects_class:
                prospects = [p for p in prospects if p.class_rank and p.class_rank <= args.prospects_class]
            if args.prospects_region:
                prospects = [p for p in prospects if (p.region or "").lower() == args.prospects_region.lower()]
            if args.prospects_interest_min is not None:
                prospects = [p for p in prospects if p.interest >= args.prospects_interest_min]
            if args.prospects_interest_max is not None:
                prospects = [p for p in prospects if p.interest <= args.prospects_interest_max]
            board = sorted(prospects, key=lambda r: ((r.true_rating or 0), r.interest), reverse=True)[:15]
            for rec in board:
                logger.info(
                    "AI Prospect: %s | Team:%s True:%.1f Public:%.1f Rank:%s Region:%s Interest:%.2f Visits:%s Offers:%s",
                    rec.player_id,
                    rec.team_id,
                    rec.true_rating or 0.0,
                    rec.public_rating or 0.0,
                    rec.class_rank,
                    rec.region,
                    rec.interest,
                    rec.visit_history,
                    rec.offer_history,
                )

        if args.show_standings:
            standings = compute_standings(box_scores)
            for team_id, rec in standings.items():
                logger.info("Standings: %s W:%s L:%s PF:%s PA:%s", team_id, rec["wins"], rec["losses"], rec["points_for"], rec["points_against"])

        if args.show_boxes:
            for box in box_scores:
                logger.info(
                    "Box: %s %s-%s (%s vs %s)",
                    box.game_id,
                    box.home_score,
                    box.away_score,
                    box.home_team_id,
                    box.away_team_id,
                )
                payload = box.payload or {}
                players_payload = payload.get("players", {})
                for pid, line in players_payload.items():
                    logger.info(
                        "  %s: MIN:%.1f PTS:%s REB:%s AST:%s STL:%s BLK:%s TOV:%s 3PM/3PA:%s/%s FTM/FTA:%s/%s TS%%:%.3f USG:%.3f AST%%:%.3f ORtg:%.1f DRtg:%.1f",
                        pid,
                        line.get("minutes", 0.0),
                        line.get("points", 0),
                        line.get("rebounds", 0),
                        line.get("assists", 0),
                        line.get("steals", 0),
                        line.get("blocks", 0),
                        line.get("turnovers", 0),
                        line.get("three_m", 0),
                        line.get("three_a", 0),
                        line.get("ftm", 0),
                        line.get("fta", 0),
                        line.get("ts_pct", 0.0),
                        line.get("usage", 0.0),
                        line.get("ast_pct", 0.0),
                        line.get("ortg", 0.0),
                        line.get("drtg", 0.0),
                    )

        season_totals = aggregate_player_season_stats(box_scores)
        for pid, totals in list(season_totals.items())[:5]:
            logger.info("Season totals: %s G:%s PTS:%s REB:%s AST:%s STL:%s BLK:%s TOV:%s", pid, totals["games"], totals["points"], totals["rebounds"], totals["assists"], totals["steals"], totals["blocks"], totals["turnovers"])

        # Injury report
        injuries = {pid: pl for pid, pl in player_lookup.items() if pl.injured}
        if args.show_injuries and injuries:
            for pid, pl in injuries.items():
                status = getattr(pl, "injury_status", "injured")
                logger.info(
                    "Injury: %s status=%s severity=%s type=%s days_remaining=%s",
                    pid,
                    status,
                    getattr(pl, "injury_severity", None),
                    getattr(pl, "injury_type", None),
                    pl.injury_days,
                )

        # Update save slot last_played
        save_repo.upsert(
            save_id,
            universe_id=universe_id,
            name=args.save_name or save_id,
            world_id=world_id,
            last_played_at=datetime.now().isoformat(),
        )

        logger.info("Demo simulation finished. Scores and aggregates saved to universe %s (save %s).", universe_id, save_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
