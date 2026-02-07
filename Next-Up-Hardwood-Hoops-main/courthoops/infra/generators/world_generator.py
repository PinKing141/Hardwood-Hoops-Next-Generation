from typing import List

from courthoops.domain.coach.entity import Coach
from courthoops.domain.player.entity import Player, PlayerAttributes, PlayerPersonality, PlayerTendencies
from courthoops.domain.team.entity import Team
from courthoops.infra.utils.rng import IRNG
from courthoops.infra.generators.city_service import CityService


class WorldGenerator:
    """Creates initial HS, AAU, and College ecosystems."""

    def __init__(
        self,
        player_repo,
        team_repo,
        coach_repo,
        rng: IRNG,
        city_service: CityService | None = None,
        hs_team_count: int = 4,
        aau_team_count: int = 3,
        hs_roster_size: int = 8,
        aau_roster_size: int = 8,
        hs_prestige_top: int = 60,
        hs_prestige_floor: int = 40,
        aau_prestige_top: int = 70,
        aau_prestige_floor: int = 55,
        hs_region_bias: dict | None = None,
        aau_region_bias: dict | None = None,
        world_id: str = "WORLD",
        universe_id: str = "UNIVERSE",
    ):
        self.player_repo = player_repo
        self.team_repo = team_repo
        self.coach_repo = coach_repo
        self.rng = rng
        self.city_service = city_service
        self.hs_team_count = hs_team_count
        self.aau_team_count = aau_team_count
        self.hs_roster_size = hs_roster_size
        self.aau_roster_size = aau_roster_size
        self.hs_prestige_top = hs_prestige_top
        self.hs_prestige_floor = hs_prestige_floor
        self.aau_prestige_top = aau_prestige_top
        self.aau_prestige_floor = aau_prestige_floor
        self.hs_region_bias = hs_region_bias
        self.aau_region_bias = aau_region_bias
        self.world_id = world_id.upper()
        self.universe_id = universe_id.upper()

    def bootstrap_world(self) -> dict:
        """
        Generate a playable world with HS + AAU + D1 teams and rosters.
        D1 teams remain for legacy sims; HS/AAU populate the career schedule.
        """
        teams = self._create_teams()
        coaches = self._create_coaches(teams)
        players = self._create_players(teams)
        return {"teams": teams, "coaches": coaches, "players": players}

    def _create_teams(self) -> List[Team]:
        teams: List[Team] = []
        used_states: set[str] = set()

        def next_city(region_bias=None):
            region = self._pick_region(region_bias)
            if self.city_service:
                city = self.city_service.random_city(region=region, exclude_states=used_states)
                used_states.add(city["state_id"])
                return city["city"], city["region"], city["state_id"]
            return "Metro", "East", "XX"

        # D1 legacy teams
        for tid, prestige in (("HOME", 70), ("AWAY", 65)):
            city, region, _ = next_city()
            team_id = f"{self.world_id}-{tid}"
            name = f"{city} {tid}"
            teams.append(Team(team_id=team_id, name=name, level="D1", region=region, prestige=prestige, scholarships=13))

        # HS programs (4-6) to drive junior/senior schedules
        for idx in range(self.hs_team_count):
            city, region, state = next_city(self.hs_region_bias)
            tid = f"{self.world_id}-HS{idx+1}"
            name = f"{city} HS"
            prestige = self._scale_prestige(self.hs_prestige_top, self.hs_prestige_floor, idx, self.hs_team_count)
            teams.append(Team(team_id=tid, name=name, level="HS", region=region, prestige=prestige, scholarships=0))

        # AAU clubs (3-4) for exposure circuit
        for idx in range(self.aau_team_count):
            city, region, state = next_city(self.aau_region_bias)
            tid = f"{self.world_id}-AAU{idx+1}"
            name = f"{city} Elite"
            prestige = self._scale_prestige(self.aau_prestige_top, self.aau_prestige_floor, idx, self.aau_team_count)
            teams.append(Team(team_id=tid, name=name, level="AAU", region=region, prestige=prestige, scholarships=0))

        for team in teams:
            self.team_repo.save(team)
        return teams

    def _create_coaches(self, teams: List[Team]) -> List[Coach]:
        coaches = []
        for idx, team in enumerate(teams):
            coach = Coach(
                coach_id=f"{self.world_id}-COACH-{idx}",
                name=f"Coach {team.name}",
                offensive_iq=0.6,
                defensive_iq=0.6,
                development=0.55,
                substitution=0.5,
                recruiting=0.6,
                personality="balanced",
            )
            team.coach_id = coach.coach_id
            self.coach_repo.save(coach)
            self.team_repo.save(team)
            coaches.append(coach)
        return coaches

    def _create_players(self, teams: List[Team]) -> List[Player]:
        players: List[Player] = []
        pos_cycle = ["PG", "SG", "SF", "PF", "C"]
        for team in teams:
            if team.level == "HS":
                roster_size = self.hs_roster_size
            elif team.level == "AAU":
                roster_size = self.aau_roster_size
            else:
                roster_size = 5
            for i in range(roster_size):
                pos = pos_cycle[i % len(pos_cycle)]
                pid = f"{team.team_id}-P{i}"
                class_year = "College FR" if team.level == "D1" else ("HS JR" if i < roster_size // 2 else "HS SR")
                player = Player(
                    player_id=pid,
                    name=f"Player {i} {team.name}",
                    class_year=class_year,
                    attributes=PlayerAttributes(
                        layup=self.rng.randint(40, 95),
                        dunk=self.rng.randint(25, 95),
                        inside=self.rng.randint(35, 95),
                        mid_range=self.rng.randint(30, 90),
                        three_point=self.rng.randint(25, 95),
                        free_throw=self.rng.randint(40, 95),
                        offensive_rebound=self.rng.randint(30, 90),
                        ball_control=self.rng.randint(35, 90),
                        passing=self.rng.randint(40, 90),
                        defensive_rebound=self.rng.randint(30, 90),
                        perimeter_defense=self.rng.randint(35, 90),
                        interior_defense=self.rng.randint(30, 90),
                        steal=self.rng.randint(30, 90),
                        block=self.rng.randint(25, 95),
                        speed=self.rng.randint(35, 95),
                        agility=self.rng.randint(35, 95),
                        vertical=self.rng.randint(25, 95),
                        strength=self.rng.randint(30, 90),
                        stamina=self.rng.randint(40, 95),
                        offensive_iq=self.rng.randint(40, 90),
                        defensive_iq=self.rng.randint(40, 90),
                        hustle=self.rng.randint(35, 95),
                        potential=self.rng.randint(40, 95),
                        injury_proneness=self.rng.randint(25, 80),
                        clutch=self.rng.randint(30, 95),
                        consistency=self.rng.randint(30, 90),
                        decision_discipline=self.rng.randint(35, 90),
                    ),
                    tendencies=PlayerTendencies(
                        shot_selection=self.rng.random(),
                        aggression=self.rng.random(),
                        shot_profile=self._normalized(3),
                        rim_aggression=self._normalized(2),
                        shot_creation=self._normalized(3),
                        playmaking_bias=self._normalized(3),
                        pass_profile=self._normalized(3),
                        defensive_style=self._normalized(3),
                        help_defense=self._normalized(3),
                        rebound_bias=self._normalized(3),
                        athletic_usage=self._normalized(4),
                    ),
                    personality=PlayerPersonality(
                        work_ethic=self.rng.random(),
                        coachability=self.rng.random(),
                        competitiveness=self.rng.random(),
                    ),
                    fatigue=0.0,
                    injured=False,
                    archetype="balanced",
                    stats={"position": pos, "level": team.level},
                )
                team.add_player(player.player_id)
                self.player_repo.save(player)
                players.append(player)
            self.team_repo.save(team)
        return players

    def _scale_prestige(self, top: int, floor: int, idx: int, count: int) -> int:
        if count <= 1:
            return top
        span = max(0, top - floor)
        step = span / max(1, count - 1)
        return max(floor, int(top - step * idx))

    def _pick_region(self, bias: dict | None):
        if not bias:
            return None
        regions = list(bias.keys())
        weights = list(bias.values())
        return self.rng.choice_weighted(regions, weights)

    def _normalized(self, n: int) -> list[float]:
        raw = [self.rng.random() + 0.01 for _ in range(n)]
        total = sum(raw)
        return [v / total for v in raw]
