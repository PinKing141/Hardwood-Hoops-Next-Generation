from typing import Iterable, Optional

from courthoops.domain.game.events import Event
from courthoops.domain.game.possession import Possession
from courthoops.domain.game.state import GameState
from courthoops.simulation.playbyplay.event_builder import EventBuilder


class GameEngine:
    """Controls clock and possession sequencing for a full game."""

    def __init__(self, possession_engine, substitution_engine, event_builder: Optional[EventBuilder] = None):
        self.possession_engine = possession_engine
        self.substitution_engine = substitution_engine
        self.event_builder = event_builder or EventBuilder()

    def simulate(self, game_state: GameState) -> Iterable[Event]:
        """Runs a lightweight loop of alternating possessions."""
        self._ensure_lineups(game_state)
        # expose team fouls for bonus logic in possession engine
        setattr(self.possession_engine, "_team_fouls", game_state.team_fouls)
        possessions = 20
        for i in range(possessions):
            offense = game_state.home_team_id if i % 2 == 0 else game_state.away_team_id
            defense = game_state.away_team_id if i % 2 == 0 else game_state.home_team_id
            possession = Possession(
                possession_id=f"{game_state.game_id}-P{i}",
                offense_team_id=offense,
                defense_team_id=defense,
                period=game_state.period,
                start_clock=game_state.clock_seconds,
            )
            offense_lineup = game_state.on_floor.get(offense, [])
            defense_lineup = game_state.on_floor.get(defense, [])
            # Skip if offense team has no healthy players
            offense_lineup = [pid for pid in offense_lineup if not game_state.injuries.get(pid, False)]
            defense_lineup = [pid for pid in defense_lineup if not game_state.injuries.get(pid, False)]
            if not offense_lineup:
                continue

            for event in self.possession_engine.run_possession(
                possession,
                offense_lineup,
                defense_lineup,
                fatigue_by_player=game_state.fatigue_by_player,
                fouls_by_player=game_state.fouls_by_player,
            ):
                self._apply_event(game_state, event)
                yield event

            self._tick_fatigue(game_state)
            sub_event = self.substitution_engine.make_substitutions(game_state)
            if sub_event:
                yield sub_event

            game_state.clock_seconds = max(0, game_state.clock_seconds - 24)
            if game_state.clock_seconds == 0:
                break
        # End of game injuries could be checked externally via InjuryService

    def _ensure_lineups(self, game_state: GameState) -> None:
        for team_id, roster in game_state.rosters.items():
            if team_id not in game_state.on_floor:
                starters = roster[:5]
                bench = roster[5:]
                game_state.on_floor[team_id] = starters
                game_state.bench[team_id] = bench
                for pid in roster:
                    game_state.fatigue_by_player.setdefault(pid, 0.0)
                    game_state.fouls_by_player.setdefault(pid, 0)
                    game_state.injuries.setdefault(pid, False)
                    game_state.minutes_played.setdefault(pid, 0.0)
                game_state.team_fouls.setdefault(team_id, 0)

    def _tick_fatigue(self, game_state: GameState) -> None:
        # Each possession ~24 seconds -> ~0.4 minutes
        possession_minutes = 24.0 / 60.0
        for team_id, lineup in game_state.on_floor.items():
            for pid in lineup:
                game_state.fatigue_by_player[pid] = game_state.fatigue_by_player.get(pid, 0.0) + 5.0
                game_state.minutes_played[pid] = game_state.minutes_played.get(pid, 0.0) + possession_minutes
            for pid in game_state.bench.get(team_id, []):
                game_state.fatigue_by_player[pid] = max(game_state.fatigue_by_player.get(pid, 0.0) - 3.0, 0.0)

    def _apply_event(self, game_state: GameState, event: Event) -> None:
        """Mutate game state based on scored events."""
        game_state.record_event(event)
        if event.event_type == "shot_made":
            team = event.payload.get("team_id")
            points = event.payload.get("points", 0)
            if team == game_state.home_team_id:
                game_state.score["home"] = game_state.score.get("home", 0) + points
            elif team == game_state.away_team_id:
                game_state.score["away"] = game_state.score.get("away", 0) + points
        elif event.event_type == "foul":
            pid = event.payload.get("player_id")
            if pid:
                game_state.fouls_by_player[pid] = game_state.fouls_by_player.get(pid, 0) + 1
            team = event.payload.get("team_id")
            if team:
                game_state.team_fouls[team] = game_state.team_fouls.get(team, 0) + 1
