import random

from courthoops.app.services.scouting_service import ScoutingService
from courthoops.app.services.season_service import aggregate_player_season_stats, compute_standings
from courthoops.app.services.build_name_service import BuildNameService
from courthoops.app.services.role_affinity_service import RoleAffinityService
from courthoops.app.services.recruiting_service import RecruitingService
from courthoops.app.services.injury_service import InjuryService
from courthoops.app.services.ai_ops_service import AIOpsService
from courthoops.app.services.progression_service import ProgressionService
from courthoops.domain.game.boxscore import BoxScore
from courthoops.domain.recruiting.models import RecruitingInterest
from courthoops.domain.player.entity import Player, PlayerAttributes, PlayerPersonality, PlayerTendencies
from courthoops.infra.generators.schedule_generator import ScheduleGenerator
from courthoops.infra.persistence.repositories.recruiting_repository import RecruitingRepository
from courthoops.infra.persistence.repositories.player_repository import PlayerRepository
from courthoops.infra.persistence.orm.session import make_session_factory
from courthoops.infra.persistence.orm.models import Base
from courthoops.infra.utils.rng import PythonRNG


def _attrs() -> PlayerAttributes:
    return PlayerAttributes(
        layup=70,
        dunk=65,
        inside=68,
        mid_range=70,
        three_point=75,
        free_throw=80,
        offensive_rebound=55,
        ball_control=75,
        passing=78,
        defensive_rebound=60,
        perimeter_defense=65,
        interior_defense=55,
        steal=55,
        block=45,
        speed=78,
        agility=76,
        vertical=72,
        strength=62,
        stamina=80,
        offensive_iq=78,
        defensive_iq=70,
        hustle=75,
        potential=80,
        injury_proneness=30,
        clutch=70,
        consistency=65,
        decision_discipline=70,
    )


def test_schedule_generation_regular_season():
    gen = ScheduleGenerator()
    levels = {"D1": ["A", "B", "C"]}
    schedule = gen.generate_regular_season(levels, games_per_pair=2)
    # 3 teams -> 3 pairings -> 6 games with home/away alternation
    assert len(schedule) == 6
    for game in schedule:
        assert game.level == "D1"
        assert game.home_team_id != game.away_team_id
        assert game.game_id


def test_exposure_career_schedule_targets_featured_and_background():
    gen = ScheduleGenerator()
    hs_teams = [f"HS{i}" for i in range(6)]
    aau_teams = [f"AAU{i}" for i in range(6)]
    schedule = gen.generate_exposure_career_schedule(hs_teams, aau_teams, rng=random.Random(1))
    featured = [g for g in schedule if g.featured]
    assert 24 <= len(featured) <= 30
    # Ensure HS phases still have background sims to avoid full watch grinds
    assert any((not g.featured) for g in schedule if g.phase and g.phase.startswith(("junior", "senior")))
    # AAU featured games carry the scouting/ranking/media tags
    assert any("high_scout_presence" in g.tags for g in schedule if g.phase == "aau")
    # National TV flags exist for interruption flow
    assert any(g.national_tv for g in schedule if g.featured)


def test_boxscore_aggregation_and_standings():
    payload = {
        "players": {
            "P1": {"points": 10, "rebounds": 5, "assists": 3, "steals": 1, "blocks": 0, "turnovers": 2, "three_m": 2, "three_a": 5},
            "P2": {"points": 15, "rebounds": 7, "assists": 4, "steals": 0, "blocks": 1, "turnovers": 1, "three_m": 1, "three_a": 3},
        },
        "teams": {},
    }
    boxes = [
        BoxScore(game_id="G1", home_team_id="A", away_team_id="B", home_score=80, away_score=75, payload=payload),
        BoxScore(game_id="G2", home_team_id="B", away_team_id="A", home_score=70, away_score=85, payload=payload),
    ]

    standings = compute_standings(boxes)
    assert standings["A"]["wins"] == 2
    assert standings["B"]["losses"] == 2

    totals = aggregate_player_season_stats(boxes)
    assert totals["P1"]["points"] == 20
    assert totals["P2"]["rebounds"] == 14
    assert totals["P1"]["three_a"] == 10


def test_scouting_report_fields():
    player = Player(
        player_id="P1",
        name="Tester",
        class_year="College FR",
        attributes=_attrs(),
        tendencies=PlayerTendencies(),
        personality=PlayerPersonality(),
    )
    report = ScoutingService().scouting_reports([player])["P1"]
    assert "public_ovr" in report
    assert "build_name" in report
    assert "role_descriptors" in report


def test_build_name_fuzzing_produces_name():
    random.seed(123)
    namer = BuildNameService(RoleAffinityService())
    for i in range(5):
        # Random normalized shot profile to exercise affinity/name generation
        vals = [random.random() for _ in range(3)]
        total = sum(vals)
        shot_profile = [v / total for v in vals]
        tendencies = PlayerTendencies(shot_profile=shot_profile)
        player = Player(
            player_id=f"P{i}",
            name=f"P{i}",
            class_year="College FR",
            attributes=_attrs(),
            tendencies=tendencies,
            personality=PlayerPersonality(),
        )
        name = namer.generate_name(player)
        assert isinstance(name, str) and len(name) > 0


def test_recruiting_decay_visits_competition():
    session_factory = make_session_factory("sqlite:///:memory:", Base.metadata)
    repo = RecruitingRepository(session_factory, universe_id="TEST")
    rng = PythonRNG(seed=42)
    service = RecruitingService(repo, rng, region_bias={"East": 0.1}, interest_decay=0.05, max_visits=1)

    interaction = service.evaluate_prospect(player_id="REC1", team_id="T1", fit_score=0.6, class_rank=50, region="East")
    assert interaction.public_rating is not None and interaction.true_rating is not None

    # Apply visit beyond cap -> visits should not exceed max_visits
    interaction = service.tick_interest(interaction, offered=True, visit=True)
    interaction = service.tick_interest(interaction, offered=False, visit=True)
    assert interaction.visits == 1

    # Decay lowers interest
    before = interaction.interest
    decayed = service.decay_interest([interaction])[0]
    assert decayed.interest <= before

    # Competition resolution picks highest interest
    other = RecruitingInterest(
        player_id="REC1",
        team_id="T2",
        interest=decayed.interest + 0.2,
        fit_score=0.5,
        offer_made=True,
        committed=False,
        visits=0,
        public_rating=decayed.public_rating,
        true_rating=decayed.true_rating,
        class_rank=decayed.class_rank,
        region=decayed.region,
    )
    repo.save(other)
    winner = service.resolve_competition([decayed, other])
    assert winner is not None and winner.team_id == "T2"


def test_injury_persistence_and_recovery():
    session_factory = make_session_factory("sqlite:///:memory:", Base.metadata)
    player_repo = PlayerRepository(session_factory, universe_id="TEST")
    player = Player(
        player_id="P1",
        name="Injured One",
        class_year="College FR",
        attributes=_attrs(),
        tendencies=PlayerTendencies(),
        personality=PlayerPersonality(),
        injured=True,
        injury_days=5,
        injury_status="sprain",
    )
    player_repo.save(player)
    loaded = player_repo.get("P1")
    assert loaded.injured is True
    assert loaded.injury_days == 5
    assert loaded.injury_status == "sprain"

    injury_service = InjuryService()
    recovered_map = injury_service.apply_season_recovery([loaded])
    # injury_days should decrement even if not recovered
    assert loaded.injury_days <= 5
    # recovered_map should return an entry for the player
    assert "P1" in recovered_map


def test_lineup_selection_orders_by_true_ovr_and_progression_soft_caps():
    p_high = Player(
        player_id="H",
        name="High",
        class_year="College FR",
        attributes=_attrs(),
        tendencies=PlayerTendencies(),
        personality=PlayerPersonality(),
    )
    p_low = Player(
        player_id="L",
        name="Low",
        class_year="College FR",
        attributes=_attrs(),
        tendencies=PlayerTendencies(),
        personality=PlayerPersonality(),
    )
    # Reduce low player's attributes to make true OVR lower
    p_low.attributes.layup = 30
    p_low.attributes.three_point = 30

    ai_ops = AIOpsService()
    lineup = ai_ops.select_lineup([p_low, p_high], starters=1)
    assert lineup["starters"][0].player_id == "H"

    # Progression soft caps: attribute above cap should grow slowly
    progression = ProgressionService()
    p_high.attributes.dunk = 95
    progression.apply_growth([p_high])
    assert p_high.attributes.dunk <= 99
    assert p_high.attributes.dunk - 95 <= 2.5  # limited growth beyond cap
