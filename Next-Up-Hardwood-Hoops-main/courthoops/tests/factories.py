import factory

from courthoops.domain.player.entity import Player, PlayerAttributes, PlayerPersonality, PlayerTendencies
from courthoops.domain.team.entity import Team
from courthoops.domain.coach.entity import Coach


class PlayerAttributesFactory(factory.Factory):
    class Meta:
        model = PlayerAttributes

    layup = 70
    dunk = 65
    inside = 68
    mid_range = 70
    three_point = 75
    free_throw = 78
    offensive_rebound = 55
    ball_control = 75
    passing = 78
    defensive_rebound = 60
    perimeter_defense = 65
    interior_defense = 55
    steal = 55
    block = 45
    speed = 78
    agility = 76
    vertical = 72
    strength = 62
    stamina = 80
    offensive_iq = 78
    defensive_iq = 70
    hustle = 75
    potential = 80
    injury_proneness = 30
    clutch = 70
    consistency = 65
    decision_discipline = 70


class PlayerFactory(factory.Factory):
    class Meta:
        model = Player

    player_id = factory.Sequence(lambda n: f"P{n}")
    name = factory.Faker("name")
    class_year = "College FR"
    attributes = factory.SubFactory(PlayerAttributesFactory)
    tendencies = PlayerTendencies()
    personality = PlayerPersonality(work_ethic=0.5, coachability=0.5, competitiveness=0.5)
    stats = factory.LazyAttribute(lambda _: {"position": "SG"})


class CoachFactory(factory.Factory):
    class Meta:
        model = Coach

    coach_id = factory.Sequence(lambda n: f"C{n}")
    name = factory.Faker("name")
    offensive_iq = 0.6
    defensive_iq = 0.6
    development = 0.55
    substitution = 0.5
    recruiting = 0.6
    personality = "balanced"


class TeamFactory(factory.Factory):
    class Meta:
        model = Team

    team_id = factory.Sequence(lambda n: f"T{n}")
    name = factory.Faker("company")
    level = "HS"
    region = "East"
    prestige = 60
    scholarships = 0

    @factory.post_generation
    def roster(self, create, extracted, **kwargs):
        if extracted:
            self.roster = extracted
        else:
            self.roster = []
