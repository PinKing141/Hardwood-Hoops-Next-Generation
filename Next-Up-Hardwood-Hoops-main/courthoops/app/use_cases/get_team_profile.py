from typing import Optional

from courthoops.domain.team.entity import Team


def get_team_profile(team_repo, team_id: str) -> Optional[Team]:
    """Fetches a team by id through the repository."""
    return team_repo.get(team_id)

