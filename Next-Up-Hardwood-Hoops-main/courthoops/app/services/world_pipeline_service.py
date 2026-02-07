import uuid
from typing import Iterable, List

from courthoops.domain.player.entity import Player, PlayerAttributes, PlayerPersonality, PlayerTendencies
from courthoops.domain.recruiting.models import RecruitingInterest
from courthoops.domain.team.entity import Team
from courthoops.infra.persistence.repositories.pipeline_repository import PipelineRepository
from courthoops.infra.persistence.repositories.recruiting_repository import RecruitingRepository
from courthoops.infra.utils.rng import IRNG
from courthoops.app.services.progression_service import ProgressionService
from courthoops.infra.generators.city_service import CityService


class WorldPipelineService:
    """
    Coordinates the yearly world pipeline (aging, recruiting, roster updates).
    This is the only class allowed to mutate world state across seasons.
    """

    def __init__(
        self,
        player_repo,
        team_repo,
        recruiting_repo: RecruitingRepository,
        pipeline_repo: PipelineRepository,
        rng: IRNG,
        progression_service: ProgressionService | None = None,
        city_service: CityService | None = None,
        logger=None,
    ):
        self.player_repo = player_repo
        self.team_repo = team_repo
        self.recruiting_repo = recruiting_repo
        self.pipeline_repo = pipeline_repo
        self.rng = rng
        self.logger = logger or (lambda msg: None)
        self.progression_service = progression_service or ProgressionService()
        self.city_service = city_service

    def advance_year(self) -> None:
        """Executes the annual pipeline flow."""
        self.logger("Starting world pipeline")
        players = self._load_players()
        teams = self._load_teams()
        position_map = self._derive_position_map(teams)

        aged_players = self._age_players(players)
        self._handle_graduations(aged_players, teams)
        vacancies = self._open_scholarships(teams)
        recruits = self._generate_recruit_pool(vacancies)
        commits = self._assign_recruits_to_teams(recruits, teams, vacancies)
        self._apply_development(aged_players)
        self.progression_service.apply_growth(aged_players, position_map=position_map)
        self._save_entities(aged_players + recruits, teams)

        pipeline_state = {"status": "completed", "commits": commits}
        self.pipeline_repo.save(pipeline_state)
        self.logger("World pipeline completed")

    # --- internal steps ---
    def _load_players(self) -> List[Player]:
        return self.player_repo.list_all()

    def _load_teams(self) -> List[Team]:
        return self.team_repo.list_all()

    def _age_players(self, players: Iterable[Player]) -> List[Player]:
        updated = []
        for player in players:
            class_year = player.class_year
            if "HS" in class_year and "SR" in class_year:
                player.class_year = "Recruit"
            elif "HS" in class_year:
                player.class_year = self._increment_class(class_year)
            elif "College" in class_year:
                player.class_year = self._increment_class(class_year)
            elif class_year == "Recruit":
                player.class_year = "Recruit"
            updated.append(player)
        return updated

    def _handle_graduations(self, players: Iterable[Player], teams: Iterable[Team]) -> None:
        """Remove graduated players from rosters; recruiting flow will replace them."""
        graduated_ids = {p.player_id for p in players if "Graduate" in p.class_year}
        for team in teams:
            team.roster = [pid for pid in team.roster if pid not in graduated_ids]

    def _open_scholarships(self, teams: Iterable[Team]) -> dict:
        vacancies = {}
        for team in teams:
            open_slots = max(team.scholarships - len(team.roster), 0)
            vacancies[team.team_id] = open_slots
        return vacancies

    def _derive_position_map(self, teams: Iterable[Team]) -> dict:
        """
        Heuristic position map from roster order: G, G, W, W, C repeating.
        Replace when real metadata exists.
        """
        positions = ["guard", "guard", "wing", "wing", "center"]
        mapping = {}
        for team in teams:
            for idx, pid in enumerate(team.roster):
                mapping[pid] = positions[idx % len(positions)]
        return mapping

    def _generate_recruit_pool(self, vacancies: dict) -> List[Player]:
        """Create recruit players sized to fill openings plus a small buffer."""
        total_needed = max(sum(vacancies.values()), 0) + 4
        recruits: List[Player] = []
        positions = ["PG", "SG", "SF", "PF", "C"]
        for idx in range(total_needed):
            pid = f"REC-{uuid.uuid4().hex[:8]}"
            city_meta = self.city_service.random_city() if getattr(self, "city_service", None) else None
            pos = self.rng.choice(positions)
            recruits.append(
                Player(
                    player_id=pid,
                    name=f"Recruit {pid}",
                    class_year="Recruit",
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
                    ),
                    personality=PlayerPersonality(
                        work_ethic=self.rng.random(),
                        coachability=self.rng.random(),
                        competitiveness=self.rng.random(),
                    ),
                    stats={
                        "home_region": city_meta["region"] if city_meta else None,
                        "home_state": city_meta["state_id"] if city_meta else None,
                        "home_city": city_meta["city"] if city_meta else None,
                        "position": pos,
                    },
                )
            )
        return recruits

    def _assign_recruits_to_teams(self, recruits: List[Player], teams: List[Team], vacancies: dict):
        """Commit recruits to teams using prestige-weighted selection."""
        commits = []
        for recruit in recruits:
            eligible = [team for team in teams if vacancies.get(team.team_id, 0) > 0]
            if not eligible:
                break
            weights = [max(team.prestige, 1) for team in eligible]
            chosen = self.rng.choice_weighted(eligible, weights=weights)
            vacancies[chosen.team_id] -= 1
            recruit.class_year = "College FR"
            chosen.add_player(recruit.player_id)
            commits.append({"player_id": recruit.player_id, "team_id": chosen.team_id})
            self.recruiting_repo.record_commitment(
                commitment=RecruitingInterest(
                    player_id=recruit.player_id,
                    team_id=chosen.team_id,
                    interest=1.0,
                    fit_score=chosen.prestige / 100.0,
                    offer_made=True,
                    committed=True,
                )
            )
        return commits

    def _apply_development(self, players: Iterable[Player]) -> None:
        """Apply a lightweight development tick influenced by potential, consistency, and decision discipline."""
        for player in players:
            growth_factor = 1 + (player.attributes.potential - 50) / 100.0
            consistency_penalty = max(0.5, player.attributes.consistency / 100.0)
            discipline_penalty = max(0.6, player.attributes.decision_discipline / 100.0)
            delta = 1 * growth_factor * consistency_penalty * discipline_penalty
            for field_name in (
                "layup",
                "dunk",
                "inside",
                "mid_range",
                "three_point",
                "free_throw",
                "offensive_rebound",
                "ball_control",
                "passing",
                "defensive_rebound",
                "perimeter_defense",
                "interior_defense",
                "steal",
                "block",
                "speed",
                "agility",
                "vertical",
                "strength",
                "stamina",
                "offensive_iq",
                "defensive_iq",
                "hustle",
                "clutch",
                "consistency",
                "decision_discipline",
            ):
                current = getattr(player.attributes, field_name)
                setattr(player.attributes, field_name, min(current + delta, 99))

    def _save_entities(self, players: Iterable[Player], teams: Iterable[Team]) -> None:
        for player in players:
            self.player_repo.save(player)
        for team in teams:
            self.team_repo.save(team)

    @staticmethod
    def _increment_class(class_year: str) -> str:
        steps = ["FR", "SO", "JR", "SR"]
        for i, step in enumerate(steps):
            if step in class_year and i + 1 < len(steps):
                return class_year.replace(step, steps[i + 1])
        return "Graduate" if "SR" in class_year else class_year
