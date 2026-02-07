from textual.app import ComposeResult
from textual.widgets import Button, Static
try:  # ScrollView location varies by version
    from textual.widgets import ScrollView  # type: ignore
except Exception:  # pragma: no cover
    from textual.scroll_view import ScrollView  # type: ignore
from textual.screen import Screen


class ConfirmScreen(Screen):
    """Simple confirmation screen showing summary text passed via push_screen."""

    def __init__(self, summary: str, errors: str = "", details: str = "", save_enabled: bool = True):
        super().__init__()
        self.summary = summary
        self.errors = errors
        self.details = details
        self.save_enabled = save_enabled

    def compose(self) -> ComposeResult:
        yield Static("Confirm Player", classes="section-title")
        if self.errors:
            yield Static(self.errors, classes="error")
        yield Static(self.summary)
        if self.details:
            sv = ScrollView()
            sv.update(self.details)
            yield sv
        if not self.save_enabled:
            yield Static("Save disabled (no repo configured); use JSON export instead. (Edit export path on main form)", classes="error")
        yield Button("Back", id="back")
        yield Button("Save", id="save", disabled=not self.save_enabled)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "save":
            self.dismiss(True)
