from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Team:
    team_id: str
    name: str
    level: str  # HS, D1, D2, D3
    region: str
    prestige: int = 0
    coach_id: Optional[str] = None
    roster: List[str] = field(default_factory=list)  # player ids
    scholarships: int = 0
    playstyle: Optional[str] = None

    def add_player(self, player_id: str) -> None:
        if player_id not in self.roster:
            self.roster.append(player_id)


