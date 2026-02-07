
"""
2K-style Character Creator (Textual) — with a visible vertical scrollbar on EVERY page.

What’s improved vs the earlier version:
- Global ScrollScreen base: every page content scrolls (scrollbar always visible).
- 2K-ish layout language: left Vitals, centre Builder/Lists, right Summary where relevant.
- Cleaner hierarchy (no debug spam on the main screens).
- Keyboard scrolling everywhere: ↑ ↓ PgUp PgDn Home End (plus mouse wheel).

Run:
  pip install textual
  python character_creator_2k_scroll.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    Rule,
    ProgressBar,
)

# ----------------------------
# Data model
# ----------------------------

ATTRIBUTE_GROUPS: List[Tuple[str, List[str]]] = [
    ("Finishing", ["Layup", "Dunk", "Inside"]),
    ("Shooting", ["Mid-Range", "Three-Point", "Free Throw"]),
    ("Playmaking", ["Ball Control", "Passing"]),
    ("Defense", ["Perimeter Defence", "Interior Defence", "Steal", "Block"]),
    ("Rebounding", ["Offensive Rebound", "Defensive Rebound"]),
    ("Athleticism", ["Speed", "Agility", "Vertical", "Strength", "Stamina"]),
    ("Mental & IQ", ["Offensive IQ", "Defensive IQ", "Hustle"]),
]
ALL_ATTRIBUTES: List[str] = [a for _, xs in ATTRIBUTE_GROUPS for a in xs]

BASE_CAPS_BY_POS: Dict[str, Dict[str, int]] = {
    "PG": {
        "Layup": 95, "Dunk": 92, "Inside": 88,
        "Mid-Range": 95, "Three-Point": 95, "Free Throw": 95,
        "Ball Control": 95, "Passing": 95,
        "Perimeter Defence": 95, "Interior Defence": 88, "Steal": 95, "Block": 80,
        "Offensive Rebound": 75, "Defensive Rebound": 80,
        "Speed": 95, "Agility": 95, "Vertical": 90, "Strength": 80, "Stamina": 95,
        "Offensive IQ": 95, "Defensive IQ": 95, "Hustle": 95,
    },
    "SG": {
        "Layup": 95, "Dunk": 95, "Inside": 90,
        "Mid-Range": 95, "Three-Point": 93, "Free Throw": 95,
        "Ball Control": 93, "Passing": 95,
        "Perimeter Defence": 96, "Interior Defence": 92, "Steal": 95, "Block": 88,
        "Offensive Rebound": 80, "Defensive Rebound": 85,
        "Speed": 95, "Agility": 95, "Vertical": 95, "Strength": 88, "Stamina": 95,
        "Offensive IQ": 95, "Defensive IQ": 95, "Hustle": 95,
    },
    "SF": {
        "Layup": 92, "Dunk": 95, "Inside": 95,
        "Mid-Range": 92, "Three-Point": 90, "Free Throw": 90,
        "Ball Control": 88, "Passing": 90,
        "Perimeter Defence": 92, "Interior Defence": 95, "Steal": 90, "Block": 92,
        "Offensive Rebound": 88, "Defensive Rebound": 92,
        "Speed": 90, "Agility": 90, "Vertical": 92, "Strength": 92, "Stamina": 92,
        "Offensive IQ": 92, "Defensive IQ": 92, "Hustle": 95,
    },
    "PF": {
        "Layup": 88, "Dunk": 95, "Inside": 95,
        "Mid-Range": 88, "Three-Point": 85, "Free Throw": 85,
        "Ball Control": 80, "Passing": 85,
        "Perimeter Defence": 88, "Interior Defence": 96, "Steal": 85, "Block": 95,
        "Offensive Rebound": 95, "Defensive Rebound": 96,
        "Speed": 85, "Agility": 85, "Vertical": 90, "Strength": 96, "Stamina": 90,
        "Offensive IQ": 90, "Defensive IQ": 92, "Hustle": 95,
    },
    "C": {
        "Layup": 85, "Dunk": 95, "Inside": 95,
        "Mid-Range": 82, "Three-Point": 78, "Free Throw": 80,
        "Ball Control": 72, "Passing": 85,
        "Perimeter Defence": 82, "Interior Defence": 98, "Steal": 80, "Block": 98,
        "Offensive Rebound": 98, "Defensive Rebound": 98,
        "Speed": 78, "Agility": 78, "Vertical": 88, "Strength": 98, "Stamina": 88,
        "Offensive IQ": 88, "Defensive IQ": 92, "Hustle": 95,
    },
}


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def normalise3(a: int, b: int, c: int) -> Tuple[int, int, int]:
    total = max(1, a + b + c)
    ra = round(a * 100 / total)
    rb = round(b * 100 / total)
    rc = 100 - ra - rb
    return ra, rb, rc


@dataclass
class BasicInfo:
    name: str = "New Player"
    position: str = "SG"
    hand: str = "Right"
    birth_month: str = "January"
    birth_day: int = 1
    hometown: str = "New York, NY"
    region: str = "East"


@dataclass
class Physicals:
    height_in: int = 76  # 6'4"
    weight_lb: int = 195
    wingspan_in: int = 79  # 6'7"

    def height_str(self) -> str:
        ft, inch = divmod(self.height_in, 12)
        return f"{ft}'{inch}\""

    def wingspan_str(self) -> str:
        ft, inch = divmod(self.wingspan_in, 12)
        return f"{ft}'{inch}\""


@dataclass
class BuilderState:
    basic: BasicInfo = field(default_factory=BasicInfo)
    physicals: Physicals = field(default_factory=Physicals)

    # Potential build numbers (builder ceiling).
    potential: Dict[str, int] = field(default_factory=lambda: {a: 60 for a in ALL_ATTRIBUTES})
    budget_total: int = 800
    budget_used: int = 0

    # Tendencies (normalised)
    shot_profile_close: int = 34
    shot_profile_mid: int = 33
    shot_profile_three: int = 33

    rim_attack_layup: int = 60
    rim_attack_dunk: int = 40

    # DNA (user-facing feel)
    dna_risk: int = 50
    dna_tempo: int = 50
    dna_physicality: int = 50
    dna_streakiness: int = 50
    dna_discipline: int = 50

    body_label: str = "Balanced Wing"
    build_name: str = "Prospect"
    archetype: str = "Balanced"
    roles: List[str] = field(default_factory=list)

    def recalc(self) -> None:
        ws_delta = self.physicals.wingspan_in - self.physicals.height_in
        if ws_delta >= 4:
            self.body_label = "Long-Arm Defender"
        elif ws_delta <= 1:
            self.body_label = "Compact Scorer"
        else:
            self.body_label = "Balanced Wing"

        off = (self.potential["Three-Point"] + self.potential["Mid-Range"] + self.potential["Layup"] + self.potential["Dunk"]) / 4
        defn = (self.potential["Perimeter Defence"] + self.potential["Steal"] + self.potential["Block"] + self.potential["Interior Defence"]) / 4
        play = (self.potential["Ball Control"] + self.potential["Passing"]) / 2

        prefix = "2 Way" if defn >= 80 else ""
        spec = "3 Level" if (self.potential["Layup"] >= 78 and self.potential["Mid-Range"] >= 78 and self.potential["Three-Point"] >= 78) else ""
        core = "Shot Creator" if (off >= 80 and play >= 75) else ("Slasher" if (self.potential["Layup"] + self.potential["Dunk"]) / 2 >= 82 else ("Playmaker" if play >= 80 else "Scorer"))
        name = " ".join([p for p in (prefix, spec, core) if p]).strip()
        self.build_name = name or "Prospect"
        self.archetype = self.body_label

        roles = []
        if self.shot_profile_three >= 38:
            roles.append("floor_spacer")
        if self.rim_attack_dunk >= 45:
            roles.append("rim_pressure")
        if defn >= 80:
            roles.append("defensive_stopper")
        self.roles = roles

# ----------------------------
# Builder maths (simple + replaceable)
# ----------------------------

def compute_modifiers_and_caps(state: BuilderState) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, str]]:
    pos = state.basic.position
    base_caps = BASE_CAPS_BY_POS[pos]
    h, w, ws = state.physicals.height_in, state.physicals.weight_lb, state.physicals.wingspan_in

    base_h = {"PG": 74, "SG": 76, "SF": 79, "PF": 82, "C": 84}[pos]
    base_w = {"PG": 185, "SG": 195, "SF": 210, "PF": 235, "C": 250}[pos]
    base_ws = base_h + 3

    dh, dw, dws = h - base_h, w - base_w, ws - base_ws

    modifiers = {a: 0 for a in ALL_ATTRIBUTES}

    # Height
    modifiers["Interior Defence"] += clamp(dh // 2, -3, 4)
    modifiers["Block"] += clamp(dh // 2, -3, 4)
    modifiers["Defensive Rebound"] += clamp(dh // 3, -2, 3)
    modifiers["Offensive Rebound"] += clamp(dh // 3, -2, 3)
    modifiers["Speed"] -= clamp(dh // 2, -1, 4)
    modifiers["Agility"] -= clamp(dh // 2, -1, 4)
    modifiers["Ball Control"] -= clamp(dh // 3, -1, 3)

    # Weight
    modifiers["Strength"] += clamp(dw // 10, -3, 5)
    modifiers["Interior Defence"] += clamp(dw // 15, -2, 3)
    modifiers["Speed"] -= clamp(dw // 20, -2, 3)
    modifiers["Agility"] -= clamp(dw // 20, -2, 3)
    modifiers["Stamina"] -= clamp(dw // 25, -1, 2)

    # Wingspan
    modifiers["Steal"] += clamp(dws // 2, -2, 4)
    modifiers["Block"] += clamp(dws // 2, -2, 4)
    modifiers["Perimeter Defence"] += clamp(dws // 3, -2, 3)
    modifiers["Defensive Rebound"] += clamp(dws // 3, -2, 3)
    modifiers["Offensive Rebound"] += clamp(dws // 4, -2, 2)
    modifiers["Three-Point"] -= clamp(dws // 4, -1, 3)
    modifiers["Ball Control"] -= clamp(dws // 4, -1, 3)

    caps = dict(base_caps)
    for a in ["Block", "Interior Defence", "Defensive Rebound", "Offensive Rebound"]:
        caps[a] = clamp(caps[a] + clamp((dh + dws) // 3, -4, 6), 60, 99)
    for a in ["Speed", "Agility", "Ball Control", "Three-Point"]:
        caps[a] = clamp(caps[a] - clamp((dh + max(0, dw // 10) + max(0, dws)) // 6, 0, 6), 60, 99)

    cost_bias = {a: "—" for a in ALL_ATTRIBUTES}
    for a in ALL_ATTRIBUTES:
        delta = caps[a] - base_caps[a]
        if delta >= 2:
            cost_bias[a] = "DOWN"
        elif delta <= -2:
            cost_bias[a] = "UP"
        else:
            cost_bias[a] = "—"

    return modifiers, caps, cost_bias


def compute_public_ovr_from_potential(state: BuilderState) -> float:
    weights = {
        "Finishing": 1.0,
        "Shooting": 1.0,
        "Playmaking": 1.0,
        "Defense": 1.0,
        "Rebounding": 0.8,
        "Athleticism": 1.0,
        "Mental & IQ": 0.6,
    }
    total_w = 0.0
    total = 0.0
    for group, attrs in ATTRIBUTE_GROUPS:
        w = weights.get(group, 1.0)
        avg = sum(state.potential[a] for a in attrs) / len(attrs)
        total += avg * w
        total_w += w
    return round(total / max(0.01, total_w), 1)


def compute_starting_scaled_attributes(state: BuilderState, target_start_ovr: int = 60) -> Dict[str, int]:
    pot_ovr = compute_public_ovr_from_potential(state) or 60.0
    base_factor = clamp(int((target_start_ovr / pot_ovr) * 100), 55, 80) / 100.0

    group_factor = {
        "Finishing": base_factor,
        "Shooting": base_factor - 0.05,
        "Playmaking": base_factor - 0.05,
        "Defense": base_factor + 0.03,
        "Rebounding": base_factor + 0.03,
        "Athleticism": base_factor + 0.02,
        "Mental & IQ": base_factor,
    }

    current: Dict[str, int] = {}
    for group, attrs in ATTRIBUTE_GROUPS:
        f = group_factor.get(group, base_factor)
        for a in attrs:
            floor = 45 if group in ("Shooting", "Playmaking") else 50
            current[a] = clamp(int(round(state.potential[a] * f)), floor, 99)
    return current


def bar(value: int, cap: int, width: int = 18) -> str:
    cap = max(1, cap)
    filled = int(round((value / cap) * width))
    filled = clamp(filled, 0, width)
    return "█" * filled + "░" * (width - filled)


def fmt_mod(n: int) -> str:
    if n > 0:
        return f"(+{n})"
    if n < 0:
        return f"({n})"
    return "(+0)"


# ----------------------------
# Universal scroll base screen
# ----------------------------

class ScrollWizardScreen(Screen):
    """
    Every wizard page inherits this.
    It provides:
    - A ScrollableContainer with ALWAYS-VISIBLE vertical scrollbar
    - Global scroll key bindings
    """
    BINDINGS = [
        ("up", "scroll_up", "Scroll up"),
        ("down", "scroll_down", "Scroll down"),
        ("pageup", "page_up", "Page up"),
        ("pagedown", "page_down", "Page down"),
        ("home", "scroll_home", "Top"),
        ("end", "scroll_end", "Bottom"),
    ]

    def __init__(self, state: BuilderState, name: str | None = None):
        super().__init__(name=name)
        self.state = state

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with ScrollableContainer(id="scroller"):
            with Vertical(id="page"):
                yield from self.compose_page()
        yield Footer()

    def compose_page(self) -> ComposeResult:
        yield Label("Override compose_page()", classes="title")

    # Scroll actions (work on every page)
    def _scroller(self) -> ScrollableContainer:
        return self.query_one("#scroller", ScrollableContainer)

    def action_scroll_up(self) -> None:
        self._scroller().scroll_up()

    def action_scroll_down(self) -> None:
        self._scroller().scroll_down()

    def action_page_up(self) -> None:
        self._scroller().scroll_page_up()

    def action_page_down(self) -> None:
        self._scroller().scroll_page_down()

    def action_scroll_home(self) -> None:
        self._scroller().scroll_home()

    def action_scroll_end(self) -> None:
        self._scroller().scroll_end()

# ----------------------------
# Screens (2K-ish layout)
# ----------------------------

class BasicInfoScreen(ScrollWizardScreen):
    def compose_page(self) -> ComposeResult:
        yield Label("1) Basic Info", classes="title")
        yield Label("Keep it simple. No ratings yet.", classes="subtitle")
        yield Rule()

        with Horizontal(classes="cols"):
            with Vertical(classes="panel col"):
                yield Label("Identity", classes="panel-title")
                yield Label("Name")
                yield Input(value=self.state.basic.name, id="name")

                yield Label("Position")
                yield Select([(p, p) for p in ["PG", "SG", "SF", "PF", "C"]], value=self.state.basic.position, id="pos")

                yield Label("Hand")
                yield Select([( "Right", "Right"), ("Left", "Left")], value=self.state.basic.hand, id="hand")

            with Vertical(classes="panel col"):
                yield Label("Background", classes="panel-title")
                yield Label("Birth month")
                yield Select([(m, m) for m in ["January", "February", "March", "April", "May", "June", "July",
                                              "August", "September", "October", "November", "December"]],
                             value=self.state.basic.birth_month, id="bmonth")
                yield Label("Birth day")
                yield Input(value=str(self.state.basic.birth_day), id="bday")

                yield Label("Hometown")
                yield Input(value=self.state.basic.hometown, id="home")

                yield Label("Region")
                yield Select([(r, r) for r in ["East", "South", "Midwest", "West"]], value=self.state.basic.region, id="region")

        yield Rule()
        with Horizontal(classes="actions"):
            yield Button("Continue", id="next", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "next":
            return

        self.state.basic.name = self.query_one("#name", Input).value.strip() or "New Player"
        self.state.basic.position = self.query_one("#pos", Select).value or "SG"
        self.state.basic.hand = self.query_one("#hand", Select).value or "Right"
        self.state.basic.birth_month = self.query_one("#bmonth", Select).value or "January"
        try:
            self.state.basic.birth_day = clamp(int(self.query_one("#bday", Input).value), 1, 31)
        except ValueError:
            self.state.basic.birth_day = 1
        self.state.basic.hometown = self.query_one("#home", Input).value.strip() or "New York, NY"
        self.state.basic.region = self.query_one("#region", Select).value or "East"
        self.state.recalc()
        self.app.push_screen("physicals")


class PhysicalProfileScreen(ScrollWizardScreen):
    def compose_page(self) -> ComposeResult:
        yield Label("2) Physical Profile", classes="title")
        yield Label("Adjust body first. Everything below updates live.", classes="subtitle")
        yield Rule()

        with Horizontal(classes="cols"):
            with Vertical(classes="panel left"):
                yield Label("Player Vitals", classes="panel-title")
                yield Static(self._vitals_text(), id="vitals")

                yield Rule(line_style="heavy")
                yield Label("Body Controls", classes="panel-title")

                yield Static(self._stepper_text(), id="steps")

                with Horizontal(classes="actions"):
                    yield Button("Height −", id="h-")
                    yield Button("Height +", id="h+", variant="primary")
                with Horizontal(classes="actions"):
                    yield Button("Weight −", id="w-")
                    yield Button("Weight +", id="w+", variant="primary")
                with Horizontal(classes="actions"):
                    yield Button("Wingspan −", id="ws-")
                    yield Button("Wingspan +", id="ws+", variant="primary")

            with Vertical(classes="panel centre"):
                yield Label("Live Preview (caps & key modifiers)", classes="panel-title")
                yield Static(self._preview_text(), id="preview")

            with Vertical(classes="panel right"):
                yield Label("Quick Notes", classes="panel-title")
                yield Static(
                    "This screen is only about your body.\n\n"
                    "Next you’ll see attribute ceilings (preview), then you’ll build the 99-OVR potential.",
                    id="notes",
                )

        yield Rule()
        with Horizontal(classes="actions"):
            yield Button("Back", id="back")
            yield Button("Continue", id="next", variant="primary")

    def _vitals_text(self) -> str:
        b = self.state.basic
        p = self.state.physicals
        return (
            f"[b]{b.name}[/b]\n"
            f"{b.position} | Hand: {b.hand}\n"
            f"Birth: {b.birth_month} {b.birth_day}\n"
            f"Hometown: {b.hometown} ({b.region})\n\n"
            f"Height: {p.height_str()}\n"
            f"Weight: {p.weight_lb} lbs\n"
            f"Wingspan: {p.wingspan_str()}\n"
            f"Body: {self.state.body_label}"
        )

    def _stepper_text(self) -> str:
        p = self.state.physicals
        return (
            f"Height:   [b]{p.height_str()}[/b]\n"
            f"Weight:   [b]{p.weight_lb} lbs[/b]\n"
            f"Wingspan: [b]{p.wingspan_str()}[/b]"
        )

    def _preview_text(self) -> str:
        mods, caps, cost = compute_modifiers_and_caps(self.state)
        key = ["Three-Point", "Ball Control", "Speed", "Agility", "Strength",
               "Perimeter Defence", "Interior Defence", "Steal", "Block",
               "Offensive Rebound", "Defensive Rebound"]

        lines = []
        lines.append("[b]Key modifiers[/b]")
        any_mod = False
        for a in key:
            m = mods.get(a, 0)
            if m:
                lines.append(f"• {a}: {m:+d}")
                any_mod = True
        if not any_mod:
            lines.append("• None")

        lines.append("\n[b]Key caps[/b]")
        for a in key:
            lines.append(f"• {a}: {caps.get(a, 95)}")

        lines.append("\n[b]Cost bias (preview)[/b]")
        for a in ["Ball Control", "Three-Point", "Block", "Interior Defence", "Speed", "Agility"]:
            lines.append(f"• {a}: {cost.get(a, '—')}")
        return "\n".join(lines)

    def _refresh(self) -> None:
        self.state.recalc()
        self.query_one("#vitals", Static).update(self._vitals_text())
        self.query_one("#steps", Static).update(self._stepper_text())
        self.query_one("#preview", Static).update(self._preview_text())

    def _adjust_height(self, delta: int) -> None:
        pos = self.state.basic.position
        lo, hi = {"PG": (70, 78), "SG": (72, 81), "SF": (75, 84), "PF": (78, 86), "C": (80, 90)}[pos]
        self.state.physicals.height_in = clamp(self.state.physicals.height_in + delta, lo, hi)
        ws_lo, ws_hi = self.state.physicals.height_in + 0, self.state.physicals.height_in + 8
        self.state.physicals.wingspan_in = clamp(self.state.physicals.wingspan_in, ws_lo, ws_hi)
        self._refresh()

    def _adjust_weight(self, delta: int) -> None:
        pos = self.state.basic.position
        lo, hi = {"PG": (160, 220), "SG": (170, 235), "SF": (185, 250), "PF": (210, 280), "C": (225, 310)}[pos]
        self.state.physicals.weight_lb = clamp(self.state.physicals.weight_lb + delta, lo, hi)
        self._refresh()

    def _adjust_wingspan(self, delta: int) -> None:
        ws_lo, ws_hi = self.state.physicals.height_in + 0, self.state.physicals.height_in + 8
        self.state.physicals.wingspan_in = clamp(self.state.physicals.wingspan_in + delta, ws_lo, ws_hi)
        self._refresh()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "back":
            self.app.pop_screen()
        elif bid == "next":
            self.app.push_screen("potential_preview")
        elif bid == "h-":
            self._adjust_height(-1)
        elif bid == "h+":
            self._adjust_height(+1)
        elif bid == "w-":
            self._adjust_weight(-5)
        elif bid == "w+":
            self._adjust_weight(+5)
        elif bid == "ws-":
            self._adjust_wingspan(-1)
        elif bid == "ws+":
            self._adjust_wingspan(+1)

class PotentialPreviewScreen(ScrollWizardScreen):
    def compose_page(self) -> ComposeResult:
        yield Label("3A) Attribute Potential Preview", classes="title")
        yield Label("Ceilings only. No spending here.", classes="subtitle")
        yield Rule()

        mods, caps, cost = compute_modifiers_and_caps(self.state)
        self.state.recalc()

        with Horizontal(classes="cols"):
            with Vertical(classes="panel left"):
                yield Label("Vitals", classes="panel-title")
                b, p = self.state.basic, self.state.physicals
                yield Static(
                    f"[b]{b.name}[/b]\n{b.position} | {p.height_str()} | {p.weight_lb} lbs | {p.wingspan_str()}\n"
                    f"Body: {self.state.body_label}\n"
                    f"Build lean: {self.state.build_name}",
                    id="vitals_card",
                )
                yield Rule(line_style="heavy")
                yield Label("Cost bias (preview)", classes="panel-title")
                yield Static(
                    "\n".join(
                        [f"• {a}: {cost.get(a,'—')}" for a in ["Ball Control", "Three-Point", "Block", "Interior Defence", "Speed", "Agility"]]
                    ),
                    id="cost_card",
                )

            with Vertical(classes="panel centre"):
                yield Label("Ceilings", classes="panel-title")
                yield Static(self._caps_text(caps), id="caps_text")

            with Vertical(classes="panel right"):
                yield Label("Key modifiers", classes="panel-title")
                key = ["Three-Point", "Ball Control", "Speed", "Agility", "Strength", "Steal", "Block"]
                out = []
                for a in key:
                    m = mods.get(a, 0)
                    out.append(f"• {a}: {m:+d}")
                yield Static("\n".join(out), id="mod_card")

        yield Rule()
        with Horizontal(classes="actions"):
            yield Button("Back", id="back")
            yield Button("Continue", id="next", variant="primary")

    def _caps_text(self, caps: Dict[str, int]) -> str:
        lines: List[str] = []
        for group, attrs in ATTRIBUTE_GROUPS:
            lines.append(f"[b]{group.upper()}[/b]")
            lines.append("────────────────────────")
            for a in attrs:
                c = caps.get(a, 95)
                lines.append(f"{a:<18} {bar(c, 99, 20)}  Cap {c}")
            lines.append("")
        return "\n".join(lines)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "next":
            self.app.push_screen("builder")


class AttributeBuilderScreen(ScrollWizardScreen):
    def compose_page(self) -> ComposeResult:
        yield Label("3B) Attribute Builder — Potential (Target: 99 OVR)", classes="title")
        yield Label("Spend points to shape the 99-OVR ceiling. Career start will scale down to ~60 OVR.", classes="subtitle")
        yield Rule()

        self.state.recalc()
        mods, caps, cost = compute_modifiers_and_caps(self.state)
        pot_ovr = compute_public_ovr_from_potential(self.state)

        with Horizontal(classes="cols"):
            with Vertical(classes="panel left"):
                yield Label("Builder HUD", classes="panel-title")
                b, p = self.state.basic, self.state.physicals
                yield Static(
                    f"[b]{b.name}[/b]\n{b.position} | {p.height_str()} | {p.weight_lb} lbs | {p.wingspan_str()}\n"
                    f"Body: {self.state.body_label}\n"
                    f"Build: {self.state.build_name}\n",
                    id="hud_vitals",
                )

                yield Rule(line_style="heavy")
                yield Label("Budget", classes="panel-title")
                yield ProgressBar(total=self.state.budget_total, show_percentage=False, id="budget_bar")
                yield Static(f"{self.state.budget_used} / {self.state.budget_total}", id="budget_text", classes="muted")

                yield Rule(line_style="heavy")
                yield Label("OVR (Potential)", classes="panel-title")
                yield ProgressBar(total=99, show_percentage=False, id="ovr_bar")
                yield Static(f"{pot_ovr} → 99", id="ovr_text", classes="muted")

                yield Rule(line_style="heavy")
                yield Label("Select attribute", classes="panel-title")
                yield Select([(a, a) for a in ALL_ATTRIBUTES], value="Layup", id="attr_select")
                with Horizontal(classes="actions"):
                    yield Button("−1", id="minus")
                    yield Button("+1", id="plus", variant="primary")
                with Horizontal(classes="actions"):
                    yield Button("Reset build", id="reset")

            with Vertical(classes="panel centre"):
                yield Label("Attributes", classes="panel-title")
                yield Static(self._builder_text(mods, caps), id="builder_text")

            with Vertical(classes="panel right"):
                yield Label("Build Summary", classes="panel-title")
                yield Static(self._summary_text(cost, pot_ovr), id="summary_text")

                yield Rule(line_style="heavy")
                yield Label("Navigation", classes="panel-title")
                yield Static("Scroll: ↑ ↓ PgUp PgDn\nJump: Home / End\nContinue when ready.", classes="muted")

        yield Rule()
        with Horizontal(classes="actions"):
            yield Button("Back", id="back")
            yield Button("Continue", id="next", variant="primary")

    def _builder_text(self, mods: Dict[str, int], caps: Dict[str, int]) -> str:
        lines: List[str] = []
        for group, attrs in ATTRIBUTE_GROUPS:
            lines.append(f"[b]{group.upper()}[/b]")
            lines.append("────────────────────────────────────────────────")
            for a in attrs:
                base = self.state.potential[a]
                cap = caps.get(a, 95)
                m = mods.get(a, 0)
                final = clamp(base + m, 25, 99)
                lines.append(
                    f"{a:<18} {bar(base, cap, 18)}  {base:>2} {fmt_mod(m):>5} → {final:>2}   Cap {cap}"
                )
            lines.append("")
        return "\n".join(lines)

    def _summary_text(self, cost: Dict[str, str], pot_ovr: float) -> str:
        self.state.recalc()
        roles = ", ".join(self.state.roles) if self.state.roles else "—"

        mods, _, _ = compute_modifiers_and_caps(self.state)
        positives = sorted([(a, m) for a, m in mods.items() if m > 0], key=lambda x: x[1], reverse=True)[:3]
        negatives = sorted([(a, m) for a, m in mods.items() if m < 0], key=lambda x: x[1])[:3]

        lines = [
            f"Build: [b]{self.state.build_name}[/b]",
            f"Archetype: {self.state.archetype}",
            f"Potential OVR: {pot_ovr}",
            f"Roles: {roles}",
            "",
            "[b]Body strengths (mods)[/b]",
        ]
        if positives:
            lines += [f"• {a} {m:+d}" for a, m in positives]
        else:
            lines.append("• None")

        lines += ["", "[b]Body trade-offs[/b]"]
        if negatives:
            lines += [f"• {a} {m:+d}" for a, m in negatives]
        else:
            lines.append("• None")

        lines += ["", "[b]Cost bias[/b]"]
        for a in ["Ball Control", "Three-Point", "Block", "Interior Defence"]:
            lines.append(f"• {a}: {cost.get(a, '—')}")
        return "\n".join(lines)

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        self.state.recalc()
        mods, caps, cost = compute_modifiers_and_caps(self.state)
        pot_ovr = compute_public_ovr_from_potential(self.state)

        self.query_one("#builder_text", Static).update(self._builder_text(mods, caps))
        self.query_one("#summary_text", Static).update(self._summary_text(cost, pot_ovr))

        budget_bar = self.query_one("#budget_bar", ProgressBar)
        budget_bar.update(progress=self.state.budget_used)
        self.query_one("#budget_text", Static).update(f"{self.state.budget_used} / {self.state.budget_total}")

        ovr_bar = self.query_one("#ovr_bar", ProgressBar)
        ovr_bar.update(progress=int(round(pot_ovr)))
        self.query_one("#ovr_text", Static).update(f"{pot_ovr} → 99")

    def _spend(self, attr: str, delta: int) -> None:
        mods, caps, _ = compute_modifiers_and_caps(self.state)
        cap = caps.get(attr, 95)

        if delta > 0 and self.state.budget_used >= self.state.budget_total:
            return

        new_val = clamp(self.state.potential[attr] + delta, 25, cap)
        if new_val == self.state.potential[attr]:
            return

        if delta > 0:
            self.state.budget_used += 1
        else:
            self.state.budget_used = max(0, self.state.budget_used - 1)

        self.state.potential[attr] = new_val
        self._refresh()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "back":
            self.app.pop_screen()
            return
        if bid == "next":
            self.app.push_screen("tendencies")
            return
        if bid == "reset":
            self.state.potential = {a: 60 for a in ALL_ATTRIBUTES}
            self.state.budget_used = 0
            self._refresh()
            return

        sel = self.query_one("#attr_select", Select).value or "Layup"
        if bid == "plus":
            self._spend(sel, +1)
        elif bid == "minus":
            self._spend(sel, -1)


class TendenciesAndDNAScreen(ScrollWizardScreen):
    def compose_page(self) -> ComposeResult:
        yield Label("4) Tendencies & DNA", classes="title")
        yield Label("Behaviour sliders. These shape the sim, not raw ratings.", classes="subtitle")
        yield Rule()

        a, b, c = normalise3(self.state.shot_profile_close, self.state.shot_profile_mid, self.state.shot_profile_three)
        self.state.shot_profile_close, self.state.shot_profile_mid, self.state.shot_profile_three = a, b, c
        total = max(1, self.state.rim_attack_layup + self.state.rim_attack_dunk)
        self.state.rim_attack_layup = int(round(self.state.rim_attack_layup * 100 / total))
        self.state.rim_attack_dunk = 100 - self.state.rim_attack_layup

        with Horizontal(classes="cols"):
            with Vertical(classes="panel left"):
                yield Label("Tendencies", classes="panel-title")
                yield Static(self._tend_text(), id="tend_text")

                yield Rule(line_style="heavy")
                yield Label("Adjust", classes="panel-title")
                yield Label("Shot Profile (Close / Mid / Three)")
                yield Select(
                    [("Close +5", "sp_close+"), ("Close -5", "sp_close-"),
                     ("Mid +5", "sp_mid+"), ("Mid -5", "sp_mid-"),
                     ("Three +5", "sp_three+"), ("Three -5", "sp_three-")],
                    prompt="Pick adjustment…",
                    id="tend_select",
                )
                yield Button("Apply", id="apply_tend", variant="primary")

            with Vertical(classes="panel centre"):
                yield Label("DNA", classes="panel-title")
                yield Static(self._dna_text(), id="dna_text")

                yield Rule(line_style="heavy")
                yield Label("Quick DNA edit", classes="panel-title")
                yield Select(
                    [("Risk +5", "risk+"), ("Risk -5", "risk-"),
                     ("Tempo +5", "tempo+"), ("Tempo -5", "tempo-"),
                     ("Physicality +5", "phys+"), ("Physicality -5", "phys-"),
                     ("Streakiness +5", "streak+"), ("Streakiness -5", "streak-"),
                     ("Discipline +5", "disc+"), ("Discipline -5", "disc-")],
                    prompt="Pick adjustment…",
                    id="dna_select",
                )
                yield Button("Apply", id="apply_dna", variant="primary")

            with Vertical(classes="panel right"):
                yield Label("Snapshot", classes="panel-title")
                self.state.recalc()
                yield Static(
                    f"Build: [b]{self.state.build_name}[/b]\nBody: {self.state.body_label}\nRoles: {', '.join(self.state.roles) if self.state.roles else '—'}",
                    id="snap",
                )

        yield Rule()
        with Horizontal(classes="actions"):
            yield Button("Back", id="back")
            yield Button("Continue", id="next", variant="primary")

    def _tend_text(self) -> str:
        return (
            f"Shot Profile\n"
            f"• Close: {self.state.shot_profile_close}%\n"
            f"• Mid:   {self.state.shot_profile_mid}%\n"
            f"• Three: {self.state.shot_profile_three}%\n\n"
            f"Rim Attack\n"
            f"• Layup: {self.state.rim_attack_layup}%\n"
            f"• Dunk:  {self.state.rim_attack_dunk}%"
        )

    def _dna_text(self) -> str:
        return (
            f"Risk:        {self.state.dna_risk}\n"
            f"Tempo:       {self.state.dna_tempo}\n"
            f"Physicality: {self.state.dna_physicality}\n"
            f"Streakiness: {self.state.dna_streakiness}\n"
            f"Discipline:  {self.state.dna_discipline}\n"
        )

    def _apply_shot_profile(self, which: str, delta: int) -> None:
        if which == "close":
            self.state.shot_profile_close = clamp(self.state.shot_profile_close + delta, 0, 100)
        elif which == "mid":
            self.state.shot_profile_mid = clamp(self.state.shot_profile_mid + delta, 0, 100)
        elif which == "three":
            self.state.shot_profile_three = clamp(self.state.shot_profile_three + delta, 0, 100)

        a, b, c = normalise3(self.state.shot_profile_close, self.state.shot_profile_mid, self.state.shot_profile_three)
        self.state.shot_profile_close, self.state.shot_profile_mid, self.state.shot_profile_three = a, b, c

    def _apply_dna(self, field_name: str, delta: int) -> None:
        val = getattr(self.state, field_name)
        setattr(self.state, field_name, clamp(val + delta, 0, 100))

    def _refresh(self) -> None:
        self.state.recalc()
        self.query_one("#tend_text", Static).update(self._tend_text())
        self.query_one("#dna_text", Static).update(self._dna_text())
        self.query_one("#snap", Static).update(
            f"Build: [b]{self.state.build_name}[/b]\nBody: {self.state.body_label}\nRoles: {', '.join(self.state.roles) if self.state.roles else '—'}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "back":
            self.app.pop_screen()
            return
        if bid == "next":
            self.app.push_screen("scouting")
            return

        if bid == "apply_tend":
            choice = self.query_one("#tend_select", Select).value
            if choice == "sp_close+":
                self._apply_shot_profile("close", +5)
            elif choice == "sp_close-":
                self._apply_shot_profile("close", -5)
            elif choice == "sp_mid+":
                self._apply_shot_profile("mid", +5)
            elif choice == "sp_mid-":
                self._apply_shot_profile("mid", -5)
            elif choice == "sp_three+":
                self._apply_shot_profile("three", +5)
            elif choice == "sp_three-":
                self._apply_shot_profile("three", -5)
            self._refresh()

        if bid == "apply_dna":
            choice = self.query_one("#dna_select", Select).value
            mapping = {
                "risk+": ("dna_risk", +5), "risk-": ("dna_risk", -5),
                "tempo+": ("dna_tempo", +5), "tempo-": ("dna_tempo", -5),
                "phys+": ("dna_physicality", +5), "phys-": ("dna_physicality", -5),
                "streak+": ("dna_streakiness", +5), "streak-": ("dna_streakiness", -5),
                "disc+": ("dna_discipline", +5), "disc-": ("dna_discipline", -5),
            }
            if choice in mapping:
                field_name, delta = mapping[choice]
                self._apply_dna(field_name, delta)
            self._refresh()


class FinalScoutingReportScreen(ScrollWizardScreen):
    def compose_page(self) -> ComposeResult:
        yield Label("5) Final Scouting Report", classes="title")
        yield Label("What you built (potential) and how it will start in the world (~60 OVR).", classes="subtitle")
        yield Rule()

        self.state.recalc()
        mods, caps, _ = compute_modifiers_and_caps(self.state)
        pot_ovr = compute_public_ovr_from_potential(self.state)
        start = compute_starting_scaled_attributes(self.state, target_start_ovr=60)

        with Horizontal(classes="cols"):
            with Vertical(classes="panel left"):
                yield Label("Profile", classes="panel-title")
                b, p = self.state.basic, self.state.physicals
                yield Static(
                    f"[b]{b.name}[/b]\n"
                    f"{b.position} | {b.hand}\n"
                    f"{p.height_str()} | {p.weight_lb} lbs | {p.wingspan_str()}\n"
                    f"Hometown: {b.hometown} ({b.region})\n\n"
                    f"Build: [b]{self.state.build_name}[/b]\n"
                    f"Archetype: {self.state.archetype}\n"
                    f"Roles: {', '.join(self.state.roles) if self.state.roles else '—'}\n",
                    id="profile",
                )

            with Vertical(classes="panel centre"):
                yield Label("Potential vs Start", classes="panel-title")
                key = ["Layup", "Dunk", "Three-Point", "Ball Control", "Perimeter Defence", "Steal", "Block", "Speed", "Strength", "Offensive IQ", "Defensive IQ"]
                lines = [f"Potential OVR: [b]{pot_ovr}[/b] → Career start: [b]~60[/b]", ""]
                for a in key:
                    pot = self.state.potential[a]
                    m = mods.get(a, 0)
                    pot_final = clamp(pot + m, 25, 99)
                    lines.append(f"{a:<18} Pot {pot_final:>2}   Start {start.get(a, 50):>2}   Cap {caps.get(a, 95)}")
                yield Static("\n".join(lines), id="compare")

            with Vertical(classes="panel right"):
                yield Label("Play Style", classes="panel-title")
                yield Static(
                    f"Shot profile: Close {self.state.shot_profile_close}% / Mid {self.state.shot_profile_mid}% / Three {self.state.shot_profile_three}%\n"
                    f"Rim attack: Layup {self.state.rim_attack_layup}% / Dunk {self.state.rim_attack_dunk}%\n\n"
                    f"DNA:\n"
                    f"Risk {self.state.dna_risk} • Tempo {self.state.dna_tempo}\n"
                    f"Physicality {self.state.dna_physicality} • Streakiness {self.state.dna_streakiness}\n"
                    f"Discipline {self.state.dna_discipline}",
                    id="style",
                )

        yield Rule()
        with Horizontal(classes="actions"):
            yield Button("Back", id="back")
            yield Button("Confirm", id="next", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "next":
            self.app.push_screen("confirm")


class ConfirmStartScreen(ScrollWizardScreen):
    def compose_page(self) -> ComposeResult:
        yield Label("6) Confirm & Start Career", classes="title")
        yield Label("This will create the career-start attributes (~60 OVR) from your 99 potential build.", classes="subtitle")
        yield Rule()

        self.state.recalc()
        current = compute_starting_scaled_attributes(self.state, target_start_ovr=60)

        with Horizontal(classes="cols"):
            with Vertical(classes="panel left"):
                yield Label("Final Summary", classes="panel-title")
                b, p = self.state.basic, self.state.physicals
                pot_ovr = compute_public_ovr_from_potential(self.state)
                yield Static(
                    f"[b]{b.name}[/b]\n{b.position}\n"
                    f"{p.height_str()} | {p.weight_lb} lbs | {p.wingspan_str()}\n"
                    f"Build: {self.state.build_name}\n"
                    f"Potential OVR: {pot_ovr}\n",
                    id="final",
                )

            with Vertical(classes="panel centre"):
                yield Label("Career Start (sample)", classes="panel-title")
                key = ["Layup", "Dunk", "Three-Point", "Ball Control", "Perimeter Defence", "Steal", "Block", "Speed", "Strength"]
                yield Static("\n".join([f"• {a}: {current.get(a, 50)}" for a in key]), id="start_list")

            with Vertical(classes="panel right"):
                yield Label("Action", classes="panel-title")
                yield Static(
                    "In a full game, this is where you would:\n"
                    "• save the build to your database\n"
                    "• create a career profile\n"
                    "• generate rankings & recruiting context\n",
                    classes="muted",
                )
                yield Rule(line_style="heavy")
                yield Button("Start Career (demo)", id="start", variant="primary")
                yield Button("Back", id="back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "start":
            payload = {
                "basic": self.state.basic.__dict__,
                "physicals": {
                    "height_in": self.state.physicals.height_in,
                    "weight_lb": self.state.physicals.weight_lb,
                    "wingspan_in": self.state.physicals.wingspan_in,
                },
                "build": {
                    "body": self.state.body_label,
                    "name": self.state.build_name,
                    "archetype": self.state.archetype,
                    "roles": self.state.roles,
                },
                "potential_attributes": dict(self.state.potential),
                "career_start_attributes": compute_starting_scaled_attributes(self.state, target_start_ovr=60),
                "tendencies": {
                    "shot_profile": {
                        "close": self.state.shot_profile_close,
                        "mid": self.state.shot_profile_mid,
                        "three": self.state.shot_profile_three,
                    },
                    "rim_attack": {
                        "layup": self.state.rim_attack_layup,
                        "dunk": self.state.rim_attack_dunk,
                    },
                },
                "dna": {
                    "risk": self.state.dna_risk,
                    "tempo": self.state.dna_tempo,
                    "physicality": self.state.dna_physicality,
                    "streakiness": self.state.dna_streakiness,
                    "discipline": self.state.dna_discipline,
                },
            }
            self.app.log("START CAREER PAYLOAD:", payload)
            self.app.exit(message="Career started (demo). Check logs for payload.")


# ----------------------------
# App
# ----------------------------

class CharacterCreator2K(App):
    CSS = """
    Screen {
        background: #0a0f16;
        color: #e8eef7;
    }

    /* PAGE + SCROLLER */
    #scroller {
        scrollbar-gutter: stable;
        overflow-y: scroll;
        padding: 1 2;
    }
    #page {
        padding: 0;
    }

    Scrollbar {
        background: #0f1621;
    }
    Scrollbar > .scrollbar--thumb {
        background: #2b3a4a;
    }
    Scrollbar.vertical {
        width: 2;
    }

    .title {
        text-style: bold;
        color: #ffffff;
    }
    .subtitle {
        color: #aab7c6;
        margin-bottom: 1;
    }

    .panel {
        border: round #2b3a4a;
        background: #0f1621;
        padding: 1 2;
    }
    .panel-title {
        text-style: bold;
        color: #ffffff;
        margin-bottom: 1;
    }

    .cols {
        height: auto;
    }
    .left { width: 30; }
    .right { width: 30; }
    .centre { width: 1fr; }

    .actions {
        margin-top: 1;
    }

    .muted {
        color: #aab7c6;
    }
    """

    def __init__(self):
        super().__init__()
        self.state = BuilderState()
        self.state.recalc()

    def on_mount(self) -> None:
        self.install_screen(BasicInfoScreen(self.state), name="basic")
        self.install_screen(PhysicalProfileScreen(self.state), name="physicals")
        self.install_screen(PotentialPreviewScreen(self.state), name="potential_preview")
        self.install_screen(AttributeBuilderScreen(self.state), name="builder")
        self.install_screen(TendenciesAndDNAScreen(self.state), name="tendencies")
        self.install_screen(FinalScoutingReportScreen(self.state), name="scouting")
        self.install_screen(ConfirmStartScreen(self.state), name="confirm")

        self.push_screen("basic")


if __name__ == "__main__":
    CharacterCreator2K().run()
