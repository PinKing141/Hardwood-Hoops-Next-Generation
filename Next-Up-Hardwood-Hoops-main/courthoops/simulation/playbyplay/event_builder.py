import time
from typing import Any, Dict

from courthoops.domain.game.events import Event


class EventBuilder:
    """Creates domain event objects from raw simulation data."""

    def build(self, event_type: str, description: str, payload: Dict[str, Any]) -> Event:
        return Event(event_type=event_type, description=description, payload=payload, timestamp=time.time())


