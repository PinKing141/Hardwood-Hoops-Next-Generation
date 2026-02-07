from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static


class Slider(Widget):
    """Minimal numeric slider substitute for Textual versions without Slider."""

    BINDINGS = [
        Binding("left", "decrease", show=False),
        Binding("right", "increase", show=False),
        Binding("down", "decrease", show=False),
        Binding("up", "increase", show=False),
    ]

    class Changed(Message):
        def __init__(self, slider: "Slider", value: int) -> None:
            self.slider = slider
            self.value = value
            super().__init__()

    def __init__(self, *, name: str = "", value: int = 0, minimum: int = 0, maximum: int = 100, step: int = 1, id: str | None = None):
        super().__init__(id=id)
        self.label = name
        self.minimum = minimum
        self.maximum = maximum
        self.step = max(1, step)
        self._value = self._clamp(value)
        self._input: Input | None = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static(self.label or "", classes="slider-label")
            self._input = Input(value=str(self._value), placeholder=self.label, id=f"{self.id}-input" if self.id else None)
            yield self._input

    # Public property to match Textual's Slider API
    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, new: int) -> None:
        self._value = self._clamp(new)
        if self._input:
            self._input.value = str(self._value)

    def _clamp(self, val: int) -> int:
        return max(self.minimum, min(int(val), self.maximum))

    def _emit_changed(self) -> None:
        self.post_message(self.Changed(self, self._value))

    def action_increase(self) -> None:
        self.value = self._value + self.step
        self._emit_changed()

    def action_decrease(self) -> None:
        self.value = self._value - self.step
        self._emit_changed()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input is not self._input:
            return
        try:
            parsed = int(event.value)
        except ValueError:
            return
        new_val = self._clamp(parsed)
        if new_val != self._value:
            self._value = new_val
            self._emit_changed()
