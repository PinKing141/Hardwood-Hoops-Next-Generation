from dataclasses import dataclass, field


@dataclass
class RecruitingInterest:
    player_id: str
    team_id: str
    interest: float
    fit_score: float
    offer_made: bool = False
    committed: bool = False
    visits: int = 0
    visit_history: list[int] = field(default_factory=list)  # weeks of visits
    offer_history: list[int] = field(default_factory=list)  # weeks offers made/renewed
    public_rating: float | None = None
    true_rating: float | None = None
    class_rank: int | None = None
    region: str | None = None


@dataclass
class CommitmentDecision:
    player_id: str
    team_id: str
    committed: bool
    rationale: str = ""
