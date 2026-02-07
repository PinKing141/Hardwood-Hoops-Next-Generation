from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Event:
    event_type: str
    description: str
    payload: Dict[str, Any]
    timestamp: float


