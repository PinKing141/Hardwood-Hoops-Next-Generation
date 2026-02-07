from typing import Callable, List, Optional, Union

from sqlalchemy import select
from sqlalchemy.orm import Session

from courthoops.domain.recruiting.models import CommitmentDecision, RecruitingInterest
from courthoops.infra.persistence.orm.models import RecruitingRow


class RecruitingRepository:
    """Loads and persists recruiting interactions."""

    def __init__(self, session_factory: Callable[[], Session], universe_id: str = "UNIVERSE"):
        self._session_factory = session_factory
        self.universe_id = universe_id

    def get(self, player_id: str, team_id: str) -> Optional[RecruitingInterest]:
        with self._session_factory() as session:
            stmt = select(RecruitingRow).where(
                RecruitingRow.player_id == player_id,
                RecruitingRow.team_id == team_id,
                RecruitingRow.universe_id == self.universe_id,
            )
            row = session.scalars(stmt).first()
            if not row:
                return None
            return self._to_domain(row)

    def save(self, interaction: RecruitingInterest) -> None:
        with self._session_factory() as session:
            stmt = select(RecruitingRow).where(
                RecruitingRow.player_id == interaction.player_id,
                RecruitingRow.team_id == interaction.team_id,
                RecruitingRow.universe_id == self.universe_id,
            )
            row = session.scalars(stmt).first() or RecruitingRow(
                player_id=interaction.player_id, team_id=interaction.team_id, universe_id=self.universe_id
            )
            row.interest = interaction.interest
            row.fit_score = interaction.fit_score
            row.offer_made = interaction.offer_made
            row.committed = interaction.committed
            row.visits = interaction.visits
            row.public_rating = interaction.public_rating
            row.true_rating = interaction.true_rating
            row.class_rank = interaction.class_rank
            row.region = interaction.region
            row.visit_history = list(getattr(interaction, "visit_history", []) or [])
            row.offer_history = list(getattr(interaction, "offer_history", []) or [])
            row.universe_id = self.universe_id
            session.add(row)
            session.commit()

    def list_for_player(self, player_id: str) -> List[RecruitingInterest]:
        with self._session_factory() as session:
            stmt = select(RecruitingRow).where(RecruitingRow.player_id == player_id, RecruitingRow.universe_id == self.universe_id)
            return [self._to_domain(row) for row in session.scalars(stmt).all()]

    def list_for_team(self, team_id: str) -> List[RecruitingInterest]:
        with self._session_factory() as session:
            stmt = select(RecruitingRow).where(RecruitingRow.team_id == team_id, RecruitingRow.universe_id == self.universe_id)
            return [self._to_domain(row) for row in session.scalars(stmt).all()]

    def list_all(self) -> List[RecruitingInterest]:
        with self._session_factory() as session:
            rows = session.query(RecruitingRow).filter(RecruitingRow.universe_id == self.universe_id).all()
            return [self._to_domain(r) for r in rows]

    @staticmethod
    def _to_domain(row: RecruitingRow) -> RecruitingInterest:
        return RecruitingInterest(
            player_id=row.player_id,
            team_id=row.team_id,
            interest=row.interest,
            fit_score=row.fit_score,
            offer_made=row.offer_made,
            committed=row.committed,
            visits=row.visits,
            public_rating=row.public_rating,
            true_rating=row.true_rating,
            class_rank=row.class_rank,
            region=row.region,
            visit_history=row.visit_history or [],
            offer_history=row.offer_history or [],
        )

    def record_commitment(self, commitment: Union[CommitmentDecision, RecruitingInterest]) -> None:
        """Persist a commitment decision result."""
        if isinstance(commitment, CommitmentDecision):
            interaction = RecruitingInterest(
                player_id=commitment.player_id,
                team_id=commitment.team_id,
                interest=1.0 if commitment.committed else 0.0,
                fit_score=0.0,
                offer_made=True,
                committed=commitment.committed,
            )
        else:
            interaction = commitment
        self.save(interaction)
