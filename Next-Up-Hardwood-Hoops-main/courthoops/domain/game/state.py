from dataclasses import dataclass, field
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .events import Event


@dataclass
class GameState:
    game_id: str
    home_team_id: str
    away_team_id: str
    period: int = 1
    clock_seconds: int = 20 * 60
    score: Dict[str, int] = field(default_factory=lambda: {"home": 0, "away": 0})
    events: List["Event"] = field(default_factory=list)
    rosters: Dict[str, List[str]] = field(default_factory=dict)
    on_floor: Dict[str, List[str]] = field(default_factory=dict)
    bench: Dict[str, List[str]] = field(default_factory=dict)
    fatigue_by_player: Dict[str, float] = field(default_factory=dict)
    fouls_by_player: Dict[str, int] = field(default_factory=dict)
    team_fouls: Dict[str, int] = field(default_factory=dict)
    injuries: Dict[str, bool] = field(default_factory=dict)
    minutes_played: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, object] = field(default_factory=dict)

    def record_event(self, event: "Event") -> None:
        self.events.append(event)
