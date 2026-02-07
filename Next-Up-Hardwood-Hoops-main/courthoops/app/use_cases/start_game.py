from typing import Dict, List, Optional

from courthoops.domain.game.state import GameState


def start_game(
    game_id: str,
    home_team_id: str,
    away_team_id: str,
    rosters: Optional[Dict[str, List[str]]] = None,
    metadata: Optional[Dict[str, object]] = None,
) -> GameState:
    """Creates a fresh game state ready for simulation."""
    return GameState(
        game_id=game_id,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        rosters=rosters or {},
        team_fouls={home_team_id: 0, away_team_id: 0},
        metadata=metadata or {},
    )
