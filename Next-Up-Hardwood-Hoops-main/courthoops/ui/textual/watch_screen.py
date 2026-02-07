from __future__ import annotations

from queue import Empty, Queue
from typing import Callable

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, TextLog, Static


class WatchModeApp(App):
    """Lightweight viewer that streams play-by-play text in watch mode."""

    CSS_PATH = None
    TITLE = "Courthoops Watch Mode"

    def __init__(self, event_queue: Queue[str], title: str | None = None, on_close: Callable[[], None] | None = None):
        super().__init__()
        self.event_queue = event_queue
        self.on_close = on_close
        if title:
            self.TITLE = title

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("Press Q to quit watch mode.", classes="hint")
            self.log = TextLog(highlight=False, markup=False, wrap=True, id="pbp-log")
            yield self.log
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(0.1, self._drain_queue)

    def _drain_queue(self) -> None:
        try:
            while True:
                msg = self.event_queue.get_nowait()
                self.log.write(msg)
        except Empty:
            return

    def on_key(self, event) -> None:  # type: ignore[override]
        if getattr(event, "key", "").lower() in ("q", "escape"):
            self.exit()

    def on_exit(self) -> None:
        if self.on_close:
            self.on_close()
