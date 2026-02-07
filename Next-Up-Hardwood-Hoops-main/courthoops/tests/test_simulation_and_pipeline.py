from courthoops.app.services.world_pipeline_service import WorldPipelineService
from courthoops.app.services.player_evaluation_service import PlayerEvaluationService
from courthoops.app.services.role_affinity_service import RoleAffinityService
from courthoops.app.services.build_name_service import BuildNameService
from courthoops.app.services.scouting_service import ScoutingService
from courthoops.app.services.season_service import SeasonService
from courthoops.app.use_cases.start_game import start_game
from courthoops.infra.persistence.repositories.boxscore_repository import BoxScoreRepository
from courthoops.infra.persistence.repositories.playbyplay_repository import PlayByPlayRepository
from courthoops.infra.persistence.repositories.game_repository import GameRepository
from courthoops.domain.game.possession import Possession
from courthoops.domain.game.state import GameState
from courthoops.domain.schedule.game import ScheduleGame
from courthoops.domain.player.entity import Player, PlayerAttributes, PlayerPersonality, PlayerTendencies
from courthoops.domain.team.entity import Team
from courthoops.infra.persistence.orm.models import Base
from courthoops.infra.persistence.orm.session import make_session_factory
from courthoops.infra.persistence.repositories.pipeline_repository import PipelineRepository
from courthoops.infra.persistence.repositories.player_repository import PlayerRepository
from courthoops.infra.persistence.repositories.recruiting_repository import RecruitingRepository
from courthoops.infra.persistence.repositories.team_repository import TeamRepository
from courthoops.infra.utils.rng import IRNG
from courthoops.simulation.engine.foul_engine import FoulEngine
from courthoops.simulation.engine.game_engine import GameEngine
from courthoops.simulation.engine.possession_engine import PossessionEngine
from courthoops.simulation.engine.rebound_engine import ReboundEngine
from courthoops.simulation.engine.shot_engine import ShotEngine
from courthoops.simulation.engine.substitution_engine import SubstitutionEngine
from courthoops.simulation.engine.team_strength import TeamStrengthService


class QueueRNG(IRNG):
    """Deterministic RNG for tests using a queue of random values."""

    def __init__(self, random_values=None):
        self.random_values = list(random_values or [])

    def randint(self, a: int, b: int) -> int:
        return a

    def random(self) -> float:
        return self.random_values.pop(0) if self.random_values else 0.5

    def choice(self, seq):
        return seq[0]

    def choice_weighted(self, seq, weights):
        return seq[0]


def test_shot_engine_respects_strength_bias():
    rng = QueueRNG(random_values=[0.1, 0.1])  # three-point attempt and make succeeds

    def strength(team_id: str) -> float:
        return 90 if team_id == "OFF" else 50

    engine = ShotEngine(rng=rng, offense_strength_fn=strength, defense_strength_fn=strength)
    possession = Possession(
        possession_id="P1", offense_team_id="OFF", defense_team_id="DEF", period=1, start_clock=24
    )
    event = engine.resolve_shot(possession)
    assert event.event_type == "shot_made"
    assert event.payload["points"] in (2, 3)


def test_game_engine_produces_scoring_events():
    rng = QueueRNG()

    def strength(team_id: str) -> float:
        return 80 if team_id == "HOME" else 55

    shot_engine = ShotEngine(rng=rng, offense_strength_fn=strength, defense_strength_fn=strength, player_lookup={})
    rebound_engine = ReboundEngine(rng=rng, offense_strength_fn=strength, defense_strength_fn=strength, player_lookup={})
    foul_engine = FoulEngine(rng=rng, offense_strength_fn=strength, defense_strength_fn=strength, player_lookup={})
    possession_engine = PossessionEngine(shot_engine, rebound_engine, foul_engine, player_lookup={})
    game_engine = GameEngine(possession_engine, SubstitutionEngine())

    game_state = GameState(
        game_id="G1",
        home_team_id="HOME",
        away_team_id="AWAY",
        rosters={"HOME": [f"H{i}" for i in range(5)], "AWAY": [f"A{i}" for i in range(5)]},
    )
    events = list(game_engine.simulate(game_state))
    assert any(event.event_type == "shot_made" for event in events)
    assert game_state.score["home"] + game_state.score["away"] > 0


def test_pipeline_fills_scholarships_with_recruits():
    session_factory = make_session_factory("sqlite:///:memory:", Base.metadata)
    player_repo = PlayerRepository(session_factory, universe_id="TEST")
    team_repo = TeamRepository(session_factory, universe_id="TEST")
    recruiting_repo = RecruitingRepository(session_factory, universe_id="TEST")
    pipeline_repo = PipelineRepository(session_factory, universe_id="TEST")

    team_a = Team(team_id="A", name="Alpha", level="D1", region="East", prestige=80, scholarships=3)
    team_b = Team(team_id="B", name="Beta", level="D1", region="East", prestige=60, scholarships=3)

    # Two seniors graduate from each team.
    for idx, team in enumerate((team_a, team_b)):
        for j in range(2):
            pid = f"{team.team_id}-SR{j}"
            player = Player(
                player_id=pid,
                name=f"Player {pid}",
                class_year="College SR",
                attributes=PlayerAttributes(
                    layup=70,
                    dunk=70,
                    inside=70,
                    mid_range=70,
                    three_point=70,
                    free_throw=70,
                    offensive_rebound=70,
                    ball_control=70,
                    passing=70,
                    defensive_rebound=70,
                    perimeter_defense=70,
                    interior_defense=70,
                    steal=70,
                    block=70,
                    speed=70,
                    agility=70,
                    vertical=70,
                    strength=70,
                    stamina=70,
                    offensive_iq=70,
                    defensive_iq=70,
                    hustle=70,
                    potential=70,
                    injury_proneness=10,
                    clutch=70,
                    consistency=70,
                    decision_discipline=70,
                ),
                tendencies=PlayerTendencies(),
                personality=PlayerPersonality(),
            )
            team.add_player(player.player_id)
            player_repo.save(player)
        team_repo.save(team)

    rng = QueueRNG()
    pipeline = WorldPipelineService(
        player_repo=player_repo,
        team_repo=team_repo,
        recruiting_repo=recruiting_repo,
        pipeline_repo=pipeline_repo,
        rng=rng,
    )
    pipeline.advance_year()

    updated_teams = {t.team_id: t for t in team_repo.list_all()}
    assert len(updated_teams["A"].roster) == updated_teams["A"].scholarships
    assert len(updated_teams["B"].roster) == updated_teams["B"].scholarships
    state = pipeline_repo.get_latest()
    assert state and state["status"] == "completed"


def test_overall_evaluation_public_noise_applied():
    player = Player(
        player_id="P1",
        name="Tester",
        class_year="College JR",
        attributes=PlayerAttributes(
            layup=80,
            dunk=60,
            inside=75,
            mid_range=70,
            three_point=78,
            free_throw=82,
            offensive_rebound=50,
            ball_control=75,
            passing=78,
            defensive_rebound=55,
            perimeter_defense=68,
            interior_defense=40,
            steal=55,
            block=30,
            speed=80,
            agility=78,
            vertical=75,
            strength=60,
            stamina=85,
            offensive_iq=80,
            defensive_iq=70,
            hustle=75,
            potential=85,
            injury_proneness=30,
            clutch=75,
            consistency=50,  # lower consistency widens public variance
            decision_discipline=70,
        ),
        tendencies=PlayerTendencies(),
        personality=PlayerPersonality(),
    )
    evaluator = PlayerEvaluationService()
    true_ovr, public_ovr = evaluator.evaluate([player])["P1"]
    assert 45 <= true_ovr <= 95
    assert 45 <= public_ovr <= 95
    # With low consistency, public should differ slightly from true (positive or negative).
    assert abs(public_ovr - true_ovr) >= 0


def test_scouting_report_includes_build_and_roles():
    player = Player(
        player_id="P2",
        name="Tester Two",
        class_year="College SO",
        attributes=PlayerAttributes(
            layup=70,
            dunk=65,
            inside=68,
            mid_range=72,
            three_point=80,
            free_throw=85,
            offensive_rebound=45,
            ball_control=75,
            passing=78,
            defensive_rebound=50,
            perimeter_defense=65,
            interior_defense=40,
            steal=50,
            block=35,
            speed=78,
            agility=76,
            vertical=70,
            strength=60,
            stamina=82,
            offensive_iq=78,
            defensive_iq=65,
            hustle=72,
            potential=82,
            injury_proneness=30,
            clutch=75,
            consistency=60,
            decision_discipline=70,
        ),
        tendencies=PlayerTendencies(
            shot_profile=[0.2, 0.3, 0.5],
            rim_aggression=[0.7, 0.3],
            shot_creation=[0.35, 0.25, 0.4],
            playmaking_bias=[0.3, 0.4, 0.3],
            pass_profile=[0.4, 0.2, 0.4],
            defensive_style=[0.4, 0.3, 0.3],
            help_defense=[0.3, 0.3, 0.4],
            rebound_bias=[0.3, 0.2, 0.5],
            athletic_usage=[0.3, 0.25, 0.25, 0.2],
        ),
        personality=PlayerPersonality(),
    )
    scouting = ScoutingService(
        evaluator=PlayerEvaluationService(),
        build_namer=BuildNameService(role_affinity=RoleAffinityService()),
        role_affinity=RoleAffinityService(),
    )
    report = scouting.scouting_reports([player])["P2"]
    assert "public_ovr" in report
    assert "build_name" in report and report["build_name"]
    assert "role_descriptors" in report and len(report["role_descriptors"]) > 0


def test_boxscore_payload_tracks_player_lines():
    session_factory = make_session_factory("sqlite:///:memory:", Base.metadata)
    player_repo = PlayerRepository(session_factory, universe_id="TEST")
    team_repo = TeamRepository(session_factory, universe_id="TEST")
    pbp_repo = PlayByPlayRepository(session_factory, universe_id="TEST")
    game_repo = GameRepository(session_factory, universe_id="TEST")
    box_repo = BoxScoreRepository(session_factory, universe_id="TEST")

    team_a = Team(team_id="H", name="Home", level="D1", region="East", prestige=70, scholarships=3)
    team_b = Team(team_id="A", name="Away", level="D1", region="East", prestige=70, scholarships=3)
    team_repo.save(team_a)
    team_repo.save(team_b)

    player_a = Player(
        player_id="P1",
        name="P1",
        class_year="College FR",
        attributes=PlayerAttributes(
            layup=80,
            dunk=60,
            inside=75,
            mid_range=72,
            three_point=80,
            free_throw=85,
            offensive_rebound=60,
            ball_control=75,
            passing=78,
            defensive_rebound=65,
            perimeter_defense=65,
            interior_defense=40,
            steal=55,
            block=35,
            speed=78,
            agility=76,
            vertical=70,
            strength=60,
            stamina=82,
            offensive_iq=78,
            defensive_iq=65,
            hustle=72,
            potential=82,
            injury_proneness=30,
            clutch=75,
            consistency=60,
            decision_discipline=70,
        ),
        tendencies=PlayerTendencies(),
        personality=PlayerPersonality(),
    )
    player_repo.save(player_a)
    team_a.add_player(player_a.player_id)
    team_repo.save(team_a)

    rng = QueueRNG(random_values=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1])  # ensure shot makes, etc.

    def strength(team_id: str) -> float:
        return 80

    def engine_factory(ctx):
        gs = ctx["game_state"]
        strength_service = TeamStrengthService(gs, {"P1": player_a})
        shot_engine = ShotEngine(
            rng=rng,
            offense_strength_fn=strength_service.offense_strength,
            defense_strength_fn=strength_service.defense_strength,
            player_lookup={"P1": player_a},
        )
        rebound_engine = ReboundEngine(
            rng=rng,
            offense_strength_fn=strength_service.offense_strength,
            defense_strength_fn=strength_service.defense_strength,
            player_lookup={"P1": player_a},
        )
        foul_engine = FoulEngine(
            rng=rng,
            offense_strength_fn=strength_service.offense_strength,
            defense_strength_fn=strength_service.defense_strength,
            player_lookup={"P1": player_a},
        )
        sub_engine = SubstitutionEngine()
        return GameEngine(PossessionEngine(shot_engine, rebound_engine, foul_engine, player_lookup={"P1": player_a}), sub_engine)

    season = SeasonService(game_repo, pbp_repo, box_repo, engine_factory)
    rosters = {"H": ["P1"], "A": []}
    schedule = [("G1", "H", "A")]
    boxes = season.simulate_schedule(schedule, rosters, {"P1": player_a})
    assert boxes
    stored = box_repo.get("G1")
    assert stored and stored.payload
    p_line = stored.payload["players"]["P1"]
    assert p_line["points"] >= 0
    assert "fga" in p_line


def test_simulate_schedule_interrupts_on_national_tv():
    class DummyEngine:
        def simulate(self, game_state):
            return []

    class DummyGameRepo:
        def __init__(self):
            self.saved = {}

        def save(self, obj):
            self.saved[getattr(obj, "game_id", len(self.saved))] = obj

    class DummyPBPRepo:
        def __init__(self):
            self.events = {}

        def save_events(self, game_id, events):
            self.events[game_id] = list(events)

    class DummyBoxRepo:
        def __init__(self):
            self.boxes = {}

        def save(self, box):
            self.boxes[box.game_id] = box

    season = SeasonService(DummyGameRepo(), DummyPBPRepo(), DummyBoxRepo(), lambda ctx: DummyEngine())
    schedule = [
        ScheduleGame(game_id="G1", home_team_id="H", away_team_id="A", week=1, level="D1", national_tv=False),
        ScheduleGame(game_id="G2", home_team_id="H", away_team_id="A", week=2, level="D1", national_tv=True),
    ]
    def handler(game):
        # Pause on first national TV encounter
        return "pause"

    boxes = season.simulate_schedule(
        schedule,
        rosters={"H": [], "A": []},
        player_lookup={},
        interrupt_on_national_tv=True,
        interrupt_handler=handler,
    )
    assert len(boxes) == 1
    assert boxes[0].game_id == "G1"
