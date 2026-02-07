from dataclasses import dataclass


@dataclass
class Coach:
    coach_id: str
    name: str
    offensive_iq: float
    defensive_iq: float
    development: float
    substitution: float
    recruiting: float
    personality: str = "balanced"


