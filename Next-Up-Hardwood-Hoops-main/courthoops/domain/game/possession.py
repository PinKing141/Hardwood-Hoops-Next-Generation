from dataclasses import dataclass


@dataclass
class Possession:
    possession_id: str
    offense_team_id: str
    defense_team_id: str
    period: int
    start_clock: int
    play_type: str | None = None

