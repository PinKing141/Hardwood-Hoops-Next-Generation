class FoulRules:
    """Logic for foul thresholds and free throw handling."""

    def is_bonus(self, foul_count: int) -> bool:
        return foul_count >= 7


