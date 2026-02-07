def recruit_player(recruiting_service, player_id: str, team_id: str):
    """Initiates or updates a recruiting interaction."""
    return recruiting_service.recruit(player_id, team_id)


