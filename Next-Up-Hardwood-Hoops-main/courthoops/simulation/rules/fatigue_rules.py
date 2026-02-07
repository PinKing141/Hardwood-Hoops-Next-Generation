class FatigueRules:
    """Determines how quickly players tire and recover."""

    def tick_fatigue(self, current: float, minutes_played: float) -> float:
        return current + minutes_played * 0.5

