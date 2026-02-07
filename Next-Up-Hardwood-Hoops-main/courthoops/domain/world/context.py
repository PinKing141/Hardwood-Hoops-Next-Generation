from dataclasses import dataclass


@dataclass
class Region:
    name: str
    strength: int = 0


@dataclass
class YearContext:
    year: int
    phase: str = "preseason"


@dataclass
class ClassAgingRules:
    min_age: int = 14
    max_age: int = 23


