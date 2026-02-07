from typing import Dict, List

from courthoops.domain.game.state import GameState
from courthoops.domain.player.entity import Player


class TeamStrengthService:
    """
    Computes offense/defense strength from on-floor lineups with fatigue penalties.
    Lower fatigue is better; fatigued players reduce team strength.
    """

    def __init__(self, game_state: GameState, player_lookup: Dict[str, Player]):
        self.game_state = game_state
        self.player_lookup = player_lookup

    def offense_strength(self, team_id: str) -> float:
        players = self._on_floor(team_id)
        if not players:
            return 50.0
        scores = []
        for pid in players:
            player = self.player_lookup.get(pid)
            if not player:
                continue
            fatigue_penalty = self._fatigue_penalty(pid, player.attributes.stamina)
            shooting = (
                0.25 * player.attributes.layup
                + 0.1 * player.attributes.dunk
                + 0.15 * player.attributes.inside
                + 0.15 * player.attributes.mid_range
                + 0.2 * player.attributes.three_point
                + 0.05 * player.attributes.offensive_rebound
                + 0.1 * player.attributes.offensive_iq
            )
            playmaking = 0.15 * player.attributes.ball_control + 0.15 * player.attributes.passing
            athletic = 0.05 * player.attributes.speed + 0.05 * player.attributes.agility + 0.05 * player.attributes.vertical
            score = shooting + playmaking + athletic - fatigue_penalty
            scores.append(score)
        return self._clamp_average(scores)

    def defense_strength(self, team_id: str) -> float:
        players = self._on_floor(team_id)
        if not players:
            return 50.0
        scores = []
        for pid in players:
            player = self.player_lookup.get(pid)
            if not player:
                continue
            fatigue_penalty = self._fatigue_penalty(pid, player.attributes.stamina)
            defense = (
                0.2 * player.attributes.perimeter_defense
                + 0.2 * player.attributes.interior_defense
                + 0.15 * player.attributes.defensive_rebound
                + 0.15 * player.attributes.steal
                + 0.15 * player.attributes.block
                + 0.1 * player.attributes.defensive_iq
                + 0.05 * player.attributes.hustle
            )
            athletic = 0.05 * player.attributes.speed + 0.05 * player.attributes.agility + 0.05 * player.attributes.vertical
            score = defense + athletic - fatigue_penalty
            scores.append(score)
        return self._clamp_average(scores)

    def _fatigue_penalty(self, pid: str, stamina: int) -> float:
        fatigue = self.game_state.fatigue_by_player.get(pid, 0.0)
        mitigation = (stamina - 50) * 0.12  # slightly stronger effect so high-stamina players last longer
        return max(fatigue - mitigation, 0.0)

    def _on_floor(self, team_id: str) -> List[str]:
        return self.game_state.on_floor.get(team_id, [])

    @staticmethod
    def _clamp_average(values: List[float]) -> float:
        if not values:
            return 50.0
        avg = sum(values) / len(values)
        return max(20.0, min(avg, 99.0))
