from dataclasses import dataclass


@dataclass
class BoxScore:
    game_id: str
    home_team_id: str
    away_team_id: str
    home_score: int
    away_score: int
    payload: dict | None = None
