from dataclasses import dataclass
from typing import Optional


@dataclass
class AppConfig:
    """Central configuration for simulation size, DB path, and RNG."""

    database_url: str = "sqlite:///courthoops.db"
    universe_id: str = "UNIVERSE"
    rng_seed: Optional[int] = None
    hs_region_count: int = 8
    d1_schools: int = 350
    d2_schools: int = 300
    d3_schools: int = 400
    # Progression knobs
    progression_max_growth: float = 2.5
    progression_decline_start_age: int = 24
    progression_decline_rate: float = 1.0
    city_db_path: str = "courthoops/data/us-cities.db"
