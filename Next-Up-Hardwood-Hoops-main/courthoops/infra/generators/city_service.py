import sqlite3
from typing import List, Dict, Optional

from courthoops.infra.utils.rng import IRNG


STATE_REGION = {
    # Simple US census region mapping for flavor
    "ME": "East", "NH": "East", "VT": "East", "MA": "East", "RI": "East", "CT": "East", "NY": "East", "NJ": "East", "PA": "East",
    "MD": "East", "DE": "East", "DC": "East", "VA": "East", "WV": "East", "NC": "East", "SC": "East", "GA": "East", "FL": "East",
    "OH": "Midwest", "MI": "Midwest", "IN": "Midwest", "IL": "Midwest", "WI": "Midwest", "MN": "Midwest", "IA": "Midwest", "MO": "Midwest", "ND": "Midwest", "SD": "Midwest", "KS": "Midwest", "NE": "Midwest",
    "KY": "South", "TN": "South", "AL": "South", "MS": "South", "LA": "South", "AR": "South", "OK": "South", "TX": "South",
    "CO": "West", "WY": "West", "MT": "West", "ID": "West", "WA": "West", "OR": "West", "CA": "West", "NV": "West", "UT": "West", "AZ": "West", "NM": "West", "AK": "West", "HI": "West",
}


class CityService:
    """Loads US cities from sqlite and provides weighted sampling."""

    def __init__(self, db_path: str, rng: IRNG):
        self.db_path = db_path
        self.rng = rng
        self._cities: List[Dict[str, object]] = []
        self._load()

    def _load(self) -> None:
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        rows = cur.execute("SELECT city,state_name,state_id,population,lat,lng FROM uscities WHERE population IS NOT NULL").fetchall()
        con.close()
        for city, state_name, state_id, pop, lat, lng in rows:
            self._cities.append(
                {
                    "city": city,
                    "state": state_name,
                    "state_id": state_id,
                    "population": pop or 1,
                    "lat": lat,
                    "lng": lng,
                    "region": STATE_REGION.get(state_id, "East"),
                }
            )

    def random_city(self, region: Optional[str] = None, exclude_states: Optional[set[str]] = None) -> Dict[str, object]:
        candidates = [c for c in self._cities if (region is None or c["region"].lower() == region.lower())]
        if exclude_states:
            candidates = [c for c in candidates if c["state_id"] not in exclude_states]
        if not candidates:
            candidates = self._cities
        weights = [c["population"] for c in candidates]
        chosen = self.rng.choice_weighted(candidates, weights)
        return chosen

    def region_bias(self) -> Dict[str, float]:
        """Return normalized population share per region for biasing recruiting/world gen."""
        totals: Dict[str, float] = {}
        for c in self._cities:
            totals[c["region"]] = totals.get(c["region"], 0) + c["population"]
        grand = sum(totals.values()) or 1.0
        return {k: v / grand for k, v in totals.items()}
