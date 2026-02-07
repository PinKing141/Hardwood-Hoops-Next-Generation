from collections import defaultdict
from typing import Dict, Iterable, List, Tuple, Optional

from courthoops.domain.recruiting.models import CommitmentDecision, RecruitingInterest
from courthoops.infra.utils.rng import IRNG


class RecruitingService:
    """
    Handles recruiting interest curves, visits/offers milestones, region bias, competition, and signing windows.
    """

    def __init__(
        self,
        recruiting_repo,
        rng: IRNG,
        region_bias: Dict[str, float] | None = None,
        interest_decay: float = 0.02,
        max_visits: int = 5,
        early_signing_weeks: Tuple[int, int] = (3, 4),
        late_signing_start: int = 8,
    ):
        self.recruiting_repo = recruiting_repo
        self.rng = rng
        self.region_bias = region_bias or {}
        self.interest_decay = interest_decay
        self.max_visits = max_visits
        self.early_signing_weeks = early_signing_weeks
        self.late_signing_start = late_signing_start

    def evaluate_prospect(self, player_id: str, team_id: str, fit_score: float, class_rank: int, region: str) -> RecruitingInterest:
        true_rating = 90 - class_rank * 0.05 + fit_score * 10
        public_rating = self._noisy_rating(true_rating, class_rank)
        base_interest = fit_score * 0.3 + self.region_bias.get(region, 0.0)
        interaction = RecruitingInterest(
            player_id=player_id,
            team_id=team_id,
            interest=base_interest,
            fit_score=fit_score,
            offer_made=False,
            committed=False,
            visits=0,
            public_rating=public_rating,
            true_rating=true_rating,
            class_rank=class_rank,
            region=region,
        )
        self.recruiting_repo.save(interaction)
        return interaction

    def region_biased_interest(self, interaction: RecruitingInterest, recruit_region: str, team_region: str) -> float:
        """Adjust interest for regional affinity: same region boosts; distant regions slight penalty."""
        if not recruit_region or not team_region:
            return interaction.interest
        if recruit_region.lower() == team_region.lower():
            return min(1.0, interaction.interest + 0.05)
        return max(0.0, interaction.interest - 0.02)

    def region_biased_interest_value(self, value: float, recruit_region: str | None, team_region: str | None) -> float:
        if not recruit_region or not team_region:
            return value
        if recruit_region.lower() == team_region.lower():
            return value + 0.05
        return max(0.0, value - 0.02)

    def apply_offer_or_visit(
        self,
        interaction: RecruitingInterest,
        player,
        team,
        offered: bool = False,
        visit: bool = False,
        week: int | None = None,
    ) -> RecruitingInterest:
        """Convenience that pulls regions from player/team for region-biased ticks."""
        recruit_region = None
        try:
            recruit_region = (player.stats or {}).get("home_region")
        except Exception:
            recruit_region = None
        team_region = getattr(team, "region", None)
        return self.tick_interest(
            interaction,
            offered=offered,
            visit=visit,
            week=week,
            recruit_region=recruit_region,
            team_region=team_region,
        )

    def tick_interest(
        self,
        interaction: RecruitingInterest,
        offered: bool = False,
        visit: bool = False,
        week: int | None = None,
        recruit_region: str | None = None,
        team_region: str | None = None,
    ) -> RecruitingInterest:
        delta = 0.05 if offered else 0.0
        if visit and interaction.visits < self.max_visits:
            delta += 0.1
            interaction.visits += 1
            if week is not None:
                interaction.visit_history.append(week)
        if offered and week is not None:
            interaction.offer_history.append(week)
        interest = interaction.interest + delta + interaction.fit_score * 0.02
        interest = self.region_biased_interest_value(interest, recruit_region, team_region)
        interaction.interest = min(1.0, interest)
        interaction.offer_made = interaction.offer_made or offered
        self.recruiting_repo.save(interaction)
        return interaction

    def decay_interest(self, interactions: Iterable[RecruitingInterest]) -> List[RecruitingInterest]:
        """Apply interest decay (e.g., weekly) to all interactions."""
        updated = []
        for inter in interactions:
            decay_amount = self.interest_decay * (1 - inter.fit_score)
            inter.interest = max(0.0, inter.interest - decay_amount)
            self.recruiting_repo.save(inter)
            updated.append(inter)
        return updated

    def commit_if_ready(self, interaction: RecruitingInterest, signing_window_open: bool = True) -> CommitmentDecision | None:
        if not signing_window_open:
            return None
        threshold = 0.75 + (interaction.visits * 0.02)
        if interaction.interest >= threshold:
            interaction.committed = True
            self.recruiting_repo.save(interaction)
            return CommitmentDecision(
                player_id=interaction.player_id,
                team_id=interaction.team_id,
                committed=True,
                rationale="Reached interest threshold",
            )
        return None

    def resolve_competition(self, interactions: Iterable[RecruitingInterest], signing_window: Optional[str] = None) -> CommitmentDecision | None:
        """
        Resolve competition for a single player across teams.
        Chooses the highest interest; tiebreaker on true_rating then random.
        """
        inter_list = list(interactions)
        if not inter_list:
            return None
        window_threshold = 0.6 if signing_window == "early" else (0.5 if signing_window == "late" else 0.0)
        inter_list.sort(
            key=lambda x: (
                x.interest,
                x.true_rating or 0.0,
                self.rng.random(),
            ),
            reverse=True,
        )
        winner = inter_list[0]
        if signing_window and winner.interest < window_threshold:
            return None
        winner.committed = True
        self.recruiting_repo.save(winner)
        rationale = f"Won {signing_window or 'open'} window competition"
        return CommitmentDecision(player_id=winner.player_id, team_id=winner.team_id, committed=True, rationale=rationale)

    def build_prospect_board(self, interactions: Iterable[RecruitingInterest]) -> List[RecruitingInterest]:
        """Sort prospects by public rating and class rank for UI/draft boards."""
        return sorted(
            interactions,
            key=lambda x: ((x.public_rating or 0), -(x.class_rank or 9999)),
            reverse=True,
        )

    def build_ai_board(self, interactions: Iterable[RecruitingInterest]) -> List[RecruitingInterest]:
        """AI-facing board sorted by true rating and interest."""
        return sorted(
            interactions,
            key=lambda x: ((x.true_rating or 0), x.interest),
            reverse=True,
        )

    def advance_week(self, interactions: Iterable[RecruitingInterest], week: int) -> List[CommitmentDecision]:
        """
        Apply decay, then resolve commitments if in an early or late window.
        Early window: weeks within early_signing_weeks (inclusive).
        Late window: week >= late_signing_start.
        """
        decayed = self.decay_interest(interactions)
        signing_window = None
        if self.early_signing_weeks[0] <= week <= self.early_signing_weeks[1]:
            signing_window = "early"
        elif week >= self.late_signing_start:
            signing_window = "late"
        decisions: List[CommitmentDecision] = []
        if signing_window:
            grouped: Dict[str, List[RecruitingInterest]] = defaultdict(list)
            for inter in decayed:
                grouped[inter.player_id].append(inter)
            for plist in grouped.values():
                decision = self.resolve_competition(plist, signing_window=signing_window)
                if decision:
                    decisions.append(decision)
        return decisions

    def open_transfer_portal(self, interactions: Iterable[RecruitingInterest], leave_probability: float = 0.1) -> List[RecruitingInterest]:
        """
        Simple portal: committed recruits with low fit/interest may reopen.
        """
        reopened: List[RecruitingInterest] = []
        for inter in interactions:
            if not inter.committed:
                continue
            leave_chance = leave_probability + (0.5 - inter.fit_score) * 0.2
            if self.rng.random() < max(0.0, leave_chance):
                inter.committed = False
                inter.offer_made = True
                inter.interest = max(inter.interest * 0.6, 0.2)
                self.recruiting_repo.save(inter)
                reopened.append(inter)
        return reopened

    def _noisy_rating(self, true_rating: float, class_rank: Optional[int]) -> float:
        noise = (self.rng.random() - 0.5) * 5.0  # ±2.5 points noise
        rank_noise = ((self.rng.random() - 0.5) * 0.1 * (class_rank or 100)) if class_rank else 0.0
        return max(25.0, min(99.0, true_rating + noise - rank_noise * 0.1))
