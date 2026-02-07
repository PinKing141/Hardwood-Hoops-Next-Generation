from typing import Optional

from courthoops.domain.player.entity import Player


def get_player_profile(player_repo, player_id: str) -> Optional[Player]:
    """Fetches a player by id through the repository."""
    return player_repo.get(player_id)

