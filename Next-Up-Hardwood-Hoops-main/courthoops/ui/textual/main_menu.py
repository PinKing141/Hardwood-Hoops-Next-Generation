from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Footer, Header, Static

from courthoops.ui.textual.character_creator import CharacterCreatorApp


class MainMenuApp(App):
    """Simple front door that can branch into the character creator."""

    CSS_PATH = None
    TITLE = "Courthoops Main Menu"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="menu-container"):
            yield Static("Welcome to Courthoops", classes="section-title")
            yield Button("Continue", id="continue")
            yield Button("New Game", id="new-game")
            yield Button("Load Game", id="load-game")
            yield Button("Settings", id="settings")
            yield Button("Exit", id="exit")
            self.status = Static("", id="menu-status", classes="hint")
            yield self.status
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "new-game":
            self.exit("new_game")
        elif bid == "continue":
            self.status.update("Continue not implemented yet.")
        elif bid == "load-game":
            self.status.update("Load Game not implemented yet.")
        elif bid == "settings":
            self.status.update("Settings not implemented yet.")
        elif bid == "exit":
            self.exit("exit")

    def on_key(self, event) -> None:  # type: ignore[override]
        key = getattr(event, "key", "").lower()
        if key in ("up", "left"):
            self._cycle_focus(forward=False)
            event.stop()
        elif key in ("down", "right"):
            self._cycle_focus(forward=True)
            event.stop()

    def _cycle_focus(self, forward: bool) -> None:
        focusables = [node for node in self.query("*") if getattr(node, "can_focus", False)]
        if not focusables:
            return
        current = self.focused if self.focused in focusables else None
        idx = focusables.index(current) if current else -1
        new_idx = (idx + (1 if forward else -1)) % len(focusables)
        focusables[new_idx].focus()


def launch_main_menu() -> None:
    """Run the menu, then branch into the character creator when chosen."""
    result = MainMenuApp().run()
    if result == "new_game":
        CharacterCreatorApp().run()


if __name__ == "__main__":
    launch_main_menu()
