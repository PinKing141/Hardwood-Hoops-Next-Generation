from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class ScheduleGame:
    game_id: str
    home_team_id: str
    away_team_id: str
    week: int
    level: str
    rivalry: bool = False
    postseason_round: Optional[str] = None
    featured: bool = True  # featured = watched/play-by-play; False = background sim
    phase: Optional[str] = None  # junior_hs, aau, senior_hs, etc.
    tags: Tuple[str, ...] = field(default_factory=tuple)  # narrative hooks (scout, ranking, media)
    national_tv: bool = False  # triggers optional sim interruption for watch/skip choice
