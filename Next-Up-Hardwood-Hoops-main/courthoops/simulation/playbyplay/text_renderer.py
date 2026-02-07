from courthoops.domain.game.events import Event


class TextRenderer:
    """Renders events as human-readable text for CLI or logs."""

    def render(self, event: Event) -> str:
        return f"[{event.event_type}] {event.description}"

