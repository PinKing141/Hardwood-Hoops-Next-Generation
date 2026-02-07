from typing import Optional, Dict

from courthoops.domain.player.entity import Player

from courthoops.domain.game.events import Event
from courthoops.simulation.playbyplay.event_builder import EventBuilder


class SubstitutionEngine:
    """Handles player swaps based on fatigue, fouls, and target minutes."""

    def __init__(
        self,
        event_builder: Optional[EventBuilder] = None,
        fatigue_threshold: float = 60.0,
        foul_threshold: int = 3,
        player_lookup: Optional[Dict[str, Player]] = None,
    ):
        self.event_builder = event_builder or EventBuilder()
        self.fatigue_threshold = fatigue_threshold
        self.foul_threshold = foul_threshold
        self.player_lookup = player_lookup or {}

    def make_substitutions(self, game_state) -> Optional[Event]:
        """
        Swap most fatigued or foul-troubled starter with freshest bench if thresholds are crossed.
        Also rotate to approach minutes allocations when available.
        """
        made_sub = False
        foul_cap = self._foul_threshold_for_clock(game_state.clock_seconds)
        fatigue_cap = self._fatigue_threshold_for_clock(game_state.clock_seconds)
        for team_id, lineup in game_state.on_floor.items():
            bench = game_state.bench.get(team_id, [])
            if not bench:
                continue

            def fatigue(pid): return game_state.fatigue_by_player.get(pid, 0.0)
            def fouls(pid): return game_state.fouls_by_player.get(pid, 0)
            def injured(pid): return game_state.injuries.get(pid, False)
            def minutes(pid): return game_state.minutes_played.get(pid, 0.0)
            def target_minutes(pid): return getattr(self.player_lookup.get(pid), "minutes_allocation", 20.0)

            candidates = [pid for pid in lineup if not injured(pid)]
            if not candidates:
                continue
            most_fatigued = max(candidates, key=lambda pid: fatigue(pid))
            fatigue_val = fatigue(most_fatigued)

            foul_trouble = sorted([pid for pid in candidates if fouls(pid) >= foul_cap], key=lambda pid: fouls(pid), reverse=True)
            target_swap = foul_trouble[0] if foul_trouble else most_fatigued

            # Minute overages: rest players well above target if bench options are fresher and under target
            over_target = [pid for pid in candidates if minutes(pid) > target_minutes(pid) + 1.0]

            available_bench = [pid for pid in bench if not injured(pid)]
            if not available_bench:
                continue
            # Prefer bench with lowest fatigue, fewer fouls, and under target minutes
            freshest = min(
                available_bench,
                key=lambda pid: (fatigue(pid), fouls(pid), minutes(pid) - target_minutes(pid)),
            )

            # Decide if we should sub: foul trouble, fatigue, or minutes management late
            should_sub = False
            if fouls(target_swap) >= foul_cap:
                should_sub = True
            elif fatigue_val >= fatigue_cap:
                should_sub = True
            elif over_target and minutes(target_swap) > target_minutes(target_swap) + 2.0 and minutes(freshest) < target_minutes(freshest) - 1.0:
                should_sub = True

            if not should_sub:
                continue

            lineup[lineup.index(target_swap)] = freshest
            bench[bench.index(freshest)] = target_swap
            made_sub = True

        if not made_sub:
            return None
        desc = "Teams adjust lineups (fatigue/foul trouble)."
        return self.event_builder.build("substitution", desc, {"period": game_state.period})

    def _foul_threshold_for_clock(self, clock_seconds: int) -> int:
        # Earlier periods: quicker to sit with fouls; late game tolerate more
        if clock_seconds > 900:  # early
            return max(self.foul_threshold - 1, 2)
        if clock_seconds > 300:  # mid
            return self.foul_threshold
        return self.foul_threshold + 1  # late, let players ride

    def _fatigue_threshold_for_clock(self, clock_seconds: int) -> float:
        # Tighten fatigue tolerance late to keep legs fresh for closing
        if clock_seconds > 900:
            return self.fatigue_threshold + 10
        if clock_seconds > 300:
            return self.fatigue_threshold
        return self.fatigue_threshold - 10
