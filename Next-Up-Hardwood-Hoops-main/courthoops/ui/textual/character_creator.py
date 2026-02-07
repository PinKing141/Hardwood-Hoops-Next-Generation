"""
Courthoops Character Creator (Textual)
Flow:
1) Basic Info
2) Physical Profile (Height / Weight / Wingspan)
3A) Attribute Potential Preview
3B) Attribute Builder (Target 99 OVR, scaled to hit 99 at caps)
4) Tendencies & DNA
5) Final Scouting Report
6) Confirm & Start Career

Run:
  pip install textual
  python character_creator.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
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
# ScrollView is not present in some Textual releases; alias to ScrollableContainer when missing.
try:  # pragma: no cover - compatibility shim
    from textual.widgets import ScrollView  # type: ignore
except Exception:  # pragma: no cover
    from textual.containers import ScrollableContainer as ScrollView  # type: ignore


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


# A simple base cap template per position (you can refine later).
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


# ----------------------------
# Cost model helpers (soft caps + physical bias)
# ----------------------------

SOFT_CAP_TIERS = (80, 90)
BUDGET_BASE = 60
# Keep the total budget leaner so you can't max everything, but still reach 99
# OVR faster with a focused build.
BUDGET_SCALE = 0.6
COST_WEIGHTS: Dict[str, float] = {
    "Three-Point": 1.6,
    "Mid-Range": 1.4,
    "Ball Control": 1.8,
    "Passing": 1.2,
    "Perimeter Defence": 1.6,
    "Interior Defence": 1.6,
    "Steal": 1.4,
    "Block": 1.4,
    "Speed": 1.6,
    "Agility": 1.5,
    "Strength": 1.5,
    "Vertical": 1.2,
    "Offensive Rebound": 1.1,
    "Defensive Rebound": 1.2,
    "Stamina": 1.0,
    "Inside": 1.0,
    "Layup": 1.2,
    "Dunk": 1.2,
    "Offensive IQ": 1.0,
    "Defensive IQ": 1.2,
    "Hustle": 0.7,
    "Free Throw": 0.6,
}


def point_cost_for_value(attr: str, value: int, cost_bias: Dict[str, str]) -> int:
    """Cost for raising an attribute to `value` (1-point step)."""
    base_cost = 1
    if value >= SOFT_CAP_TIERS[1]:
        base_cost = 3
    elif value >= SOFT_CAP_TIERS[0]:
        base_cost = 2

    bias = cost_bias.get(attr, "-")
    if bias == "UP":
        base_cost += 1
    elif bias == "DOWN":
        base_cost = max(1, base_cost - 1)

    weight = COST_WEIGHTS.get(attr, 1.0)
    weighted = int(round(base_cost * weight))
    return max(1, weighted)


def total_cost_for_build(potential: Dict[str, int], cost_bias: Dict[str, str], base: int = BUDGET_BASE) -> int:
    """Total budget cost for a potential dict relative to a base floor."""
    spend = 0
    for attr, target in potential.items():
        if target <= base:
            continue
        for val in range(base + 1, target + 1):
            spend += point_cost_for_value(attr, val, cost_bias)
    return spend


def caps_budget_total(caps: Dict[str, int], cost_bias: Dict[str, str], base: int = BUDGET_BASE) -> int:
    """Budget needed to max every attribute to its cap (scaled down to force tradeoffs)."""
    target = {a: caps.get(a, 99) for a in ALL_ATTRIBUTES}
    raw = total_cost_for_build(target, cost_bias, base=base)
    return max(200, int(raw * BUDGET_SCALE))


# ----------------------------
# Core state
# ----------------------------

@dataclass
class BasicInfo:
    first_name: str = "New"
    last_name: str = "Player"
    position: str = "SG"
    hand: str = "Right"
    birth_month: str = "January"
    birth_day: int = 1
    hometown: str = "New York, NY"
    region: str = "East"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass
class Physicals:
    height_in: int = 76  # 6'4"
    weight_lb: int = 195
    wingspan_in: int = 79  # 6'7"

    def height_str(self) -> str:
        ft = self.height_in // 12
        inch = self.height_in % 12
        return f"{ft}'{inch}\""

    def wingspan_str(self) -> str:
        ft = self.wingspan_in // 12
        inch = self.wingspan_in % 12
        return f"{ft}'{inch}\""


@dataclass
class BuilderState:
    basic: BasicInfo = field(default_factory=BasicInfo)
    physicals: Physicals = field(default_factory=Physicals)

    potential: Dict[str, int] = field(default_factory=lambda: {a: 60 for a in ALL_ATTRIBUTES})

    budget_total: int = 800
    budget_used: int = 0

    shot_profile_close: int = 34
    shot_profile_mid: int = 33
    shot_profile_three: int = 33

    rim_attack_layup: int = 60
    rim_attack_dunk: int = 40

    creation_catch: int = 34
    creation_pullup: int = 33
    creation_rim: int = 33

    play_bias_score: int = 55
    play_bias_pass: int = 45

    def_style_disciplined: int = 55
    def_style_gambler: int = 45

    rebound_crash: int = 50
    rebound_run: int = 50

    dna_risk: int = 50
    dna_tempo: int = 50
    dna_physicality: int = 50
    dna_streakiness: int = 50
    dna_discipline: int = 50

    body_label: str = "Balanced Wing"
    build_name: str = "Balanced Wing"
    archetype: str = "Balanced"
    roles: List[str] = field(default_factory=list)

    def recalc(self) -> None:
        """Recompute labels and budget totals."""
        mods, caps, cost_bias = compute_modifiers_and_caps(self)

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
        name = " ".join([p for p in [prefix, spec, core] if p]).strip()
        self.build_name = name if name else "Prospect"
        self.archetype = self.body_label

        roles = []
        if self.shot_profile_three >= 38:
            roles.append("floor_spacer")
        if self.rim_attack_dunk >= 45:
            roles.append("rim_pressure")
        if defn >= 80:
            roles.append("defensive_stopper")
        if self.rebound_crash >= 55:
            roles.append("crash_boards")
        self.roles = roles

        # Keep budget in sync with the latest caps/bias so a full spend hits 99 OVR.
        self.budget_total = caps_budget_total(caps, cost_bias, base=BUDGET_BASE)
        self.budget_used = total_cost_for_build(self.potential, cost_bias, base=BUDGET_BASE)


# ----------------------------
# Builder maths (simple, editable)
# ----------------------------

def compute_modifiers_and_caps(state: BuilderState) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, str]]:
    """
    Returns:
      modifiers: per-attribute +/- from physicals
      caps: final caps (position caps modified by physicals)
      cost_bias: per-attribute "UP/DOWN/-" based on physicals
    """
    pos = state.basic.position
    base_caps = BASE_CAPS_BY_POS[pos]
    h = state.physicals.height_in
    w = state.physicals.weight_lb
    ws = state.physicals.wingspan_in

    base_h = {"PG": 74, "SG": 76, "SF": 79, "PF": 82, "C": 84}[pos]
    base_w = {"PG": 185, "SG": 195, "SF": 210, "PF": 235, "C": 250}[pos]
    base_ws = base_h + 3

    dh = h - base_h
    dw = w - base_w
    dws = ws - base_ws

    modifiers = {a: 0 for a in ALL_ATTRIBUTES}

    modifiers["Interior Defence"] += clamp(dh // 2, -3, 4)
    modifiers["Block"] += clamp(dh // 2, -3, 4)
    modifiers["Defensive Rebound"] += clamp(dh // 3, -2, 3)
    modifiers["Offensive Rebound"] += clamp(dh // 3, -2, 3)
    modifiers["Speed"] -= clamp(dh // 2, -1, 4)
    modifiers["Agility"] -= clamp(dh // 2, -1, 4)
    modifiers["Ball Control"] -= clamp(dh // 3, -1, 3)

    modifiers["Strength"] += clamp(dw // 10, -3, 5)
    modifiers["Interior Defence"] += clamp(dw // 15, -2, 3)
    modifiers["Speed"] -= clamp(dw // 20, -2, 3)
    modifiers["Agility"] -= clamp(dw // 20, -2, 3)
    modifiers["Stamina"] -= clamp(dw // 25, -1, 2)

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

    cost_bias: Dict[str, str] = {a: "-" for a in ALL_ATTRIBUTES}
    for a in ALL_ATTRIBUTES:
        delta = caps[a] - base_caps[a]
        if delta >= 2:
            cost_bias[a] = "DOWN"
        elif delta <= -2:
            cost_bias[a] = "UP"
        else:
            cost_bias[a] = "-"

    return modifiers, caps, cost_bias


def compute_public_ovr_from_potential(state: BuilderState) -> float:
    """
    Weighted average mapped to 99 when you max out your caps.
    This keeps the builder "99 by design" even with position-specific caps.
    """
    weights = {
        "Finishing": 1.0,
        "Shooting": 1.0,
        "Playmaking": 1.0,
        "Defense": 1.0,
        "Rebounding": 0.8,
        "Athleticism": 1.0,
        "Mental & IQ": 0.6,
    }
    _, caps, _ = compute_modifiers_and_caps(state)
    total_w = 0.0
    total = 0.0
    for group, attrs in ATTRIBUTE_GROUPS:
        w = weights.get(group, 1.0)
        ratios: List[float] = []
        for a in attrs:
            cap = max(1, caps.get(a, 99))
            ratios.append(clamp(state.potential[a], 0, cap) / cap)
        ratio_avg = sum(ratios) / len(ratios)
        # Ease toward 99 a bit faster so focused builds climb OVR sooner.
        group_score = (ratio_avg ** 0.85) * 99
        total += group_score * w
        total_w += w
    return round(total / max(0.01, total_w), 1)


def compute_starting_scaled_attributes(state: BuilderState, target_start_ovr: int = 60) -> Dict[str, int]:
    pot_ovr = compute_public_ovr_from_potential(state)
    if pot_ovr <= 0:
        pot_ovr = 60.0
    base_factor = clamp(int((target_start_ovr / pot_ovr) * 100), 55, 80) / 100.0

    group_factor = {
        "Finishing": base_factor,
        "Shooting": base_factor - 0.05,
        "Playmaking": base_factor - 0.05,
        "Defense": base_factor + 0.03,
        "Rebounding": base_factor + 0.03,
        "Athleticism": base_factor + 0.02,
        "Mental & IQ": base_factor + 0.00,
    }

    current = {}
    for group, attrs in ATTRIBUTE_GROUPS:
        f = group_factor.get(group, base_factor)
        for a in attrs:
            floor = 45 if group in ("Shooting", "Playmaking") else 50
            val = int(round(state.potential[a] * f))
            current[a] = clamp(val, floor, 99)
    return current


# ----------------------------
# UI helpers
# ----------------------------

def bar(value: int, cap: int, width: int = 14) -> str:
    cap = max(1, cap)
    filled = int(round((value / cap) * width))
    filled = clamp(filled, 0, width)
    return "#" * filled + "." * (width - filled)


def fmt_mod(n: int) -> str:
    if n > 0:
        return f"(+{n})"
    if n < 0:
        return f"({n})"
    return "(+0)"


class MiniValueStepper(Static):
    """A small widget with label + value and +/- buttons."""

    def __init__(self, title: str, value_text: str, id: str):
        super().__init__(id=id)
        self.title = title
        self.value_text = value_text

    def compose(self) -> ComposeResult:
        with Horizontal(classes="stepper"):
            yield Label(self.title, classes="stepper-title")
            yield Label(self.value_text, classes="stepper-value", id=f"{self.id}-value")
            yield Button("-", id=f"{self.id}-minus", classes="stepper-btn")
            yield Button("+", id=f"{self.id}-plus", classes="stepper-btn")


# ----------------------------
# Screens
# ----------------------------

class ScrollScreen(Screen):
    """Base screen that wraps content in a scroll view with keyboard scroll actions."""

    BINDINGS = [
        ("up", "scroll_up", "Up"),
        ("down", "scroll_down", "Down"),
        ("pageup", "page_up", "Page Up"),
        ("pagedown", "page_down", "Page Down"),
        ("home", "scroll_home", "Home"),
        ("end", "scroll_end", "End"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with ScrollView(id="scroll_root") as sv:
            # Make scrollbars always visible when possible (older Textual may ignore).
            try:  # pragma: no cover - defensive compatibility
                if hasattr(sv, "vertical_scrollbar") and sv.vertical_scrollbar:
                    sv.vertical_scrollbar.auto_hide = False  # type: ignore[attr-defined]
                if hasattr(sv, "horizontal_scrollbar") and sv.horizontal_scrollbar:
                    sv.horizontal_scrollbar.auto_hide = False  # type: ignore[attr-defined]
            except Exception:
                pass
            with Vertical(id="page", classes="page"):
                yield from self.compose_page()
        yield Footer()

    def compose_page(self) -> ComposeResult:  # pragma: no cover - subclasses override
        yield

    def _scroller(self):
        return self.query_one("#scroll_root")

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


class BaseWizardScreen(ScrollScreen):
    def __init__(self, state: BuilderState, name: str | None = None):
        super().__init__(name=name)
        self.state = state

    def update_top(self) -> None:
        self.state.recalc()

    def go(self, screen_name: str) -> None:
        self.app.push_screen(screen_name)


class BasicInfoScreen(BaseWizardScreen):
    BINDINGS = ScrollScreen.BINDINGS + [("enter", "next", "Next")]

    def compose_page(self) -> ComposeResult:
        yield Label("1) Basic Info", classes="title")
        yield Rule()
        with Horizontal(classes="cols"):
            with Vertical(classes="col"):
                yield Label("First name")
                yield Input(value=self.state.basic.first_name, id="first_name")
                yield Label("Last name")
                yield Input(value=self.state.basic.last_name, id="last_name")
                yield Label("Position")
                yield Select([(p, p) for p in ["PG", "SG", "SF", "PF", "C"]], value=self.state.basic.position, id="pos")
                yield Label("Hand")
                yield Select([("Right", "Right"), ("Left", "Left")], value=self.state.basic.hand, id="hand")
            with Vertical(classes="col"):
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
        if event.button.id == "next":
            self.action_next()

    def action_next(self) -> None:
        self.state.basic.position = self.query_one("#pos", Select).value or "SG"
        self.state.basic.hand = self.query_one("#hand", Select).value or "Right"
        self.state.basic.birth_month = self.query_one("#bmonth", Select).value or "January"
        try:
            self.state.basic.birth_day = clamp(int(self.query_one("#bday", Input).value), 1, 31)
        except ValueError:
            self.state.basic.birth_day = 1
        self.state.basic.first_name = self.query_one("#first_name", Input).value.strip() or "New"
        self.state.basic.last_name = self.query_one("#last_name", Input).value.strip() or "Player"
        self.state.basic.hometown = self.query_one("#home", Input).value.strip() or "New York, NY"
        self.state.basic.region = self.query_one("#region", Select).value or "East"
        self.update_top()
        self.app.push_screen("physicals")


class PhysicalProfileScreen(BaseWizardScreen):
    def compose_page(self) -> ComposeResult:
        yield Label("2) Physical Profile (Live)", classes="title")
        yield Label("Adjust Height / Weight / Wingspan to see caps and modifiers update live.", classes="subtitle")
        yield Rule()
        with Horizontal(classes="cols"):
            with Vertical(classes="col"):
                yield Label("Vitals")
                yield Static(self._vitals_text(), id="vitals", classes="panel")
                yield Rule()
                yield Label("Height / Weight / Wingspan")
                yield MiniValueStepper("Height", self.state.physicals.height_str(), id="height")
                yield MiniValueStepper("Weight", f"{self.state.physicals.weight_lb} lbs", id="weight")
                yield MiniValueStepper("Wingspan", self.state.physicals.wingspan_str(), id="wingspan")

            with Vertical(classes="col"):
                yield Label("Preview: Modifiers & Caps")
                yield Static(self._preview_text(), id="preview", classes="panel")

        yield Rule()
        with Horizontal(classes="actions"):
            yield Button("Back", id="back")
            yield Button("Continue", id="next", variant="primary")

    def _vitals_text(self) -> str:
        b = self.state.basic
        p = self.state.physicals
        return (
            f"Name: {b.full_name}\n"
            f"Position: {b.position} | Hand: {b.hand}\n"
            f"Birth: {b.birth_month} {b.birth_day}\n"
            f"Hometown: {b.hometown}\n"
            f"Region: {b.region}\n\n"
            f"Height: {p.height_str()}\n"
            f"Weight: {p.weight_lb} lbs\n"
            f"Wingspan: {p.wingspan_str()}\n"
            f"Body: {self.state.body_label}"
        )

    def _preview_text(self) -> str:
        mods, caps, cost = compute_modifiers_and_caps(self.state)

        key = ["Three-Point", "Ball Control", "Speed", "Agility", "Strength",
               "Perimeter Defence", "Interior Defence", "Steal", "Block",
               "Offensive Rebound", "Defensive Rebound"]
        lines = ["Modifiers (key):"]
        for a in key:
            m = mods.get(a, 0)
            if m != 0:
                lines.append(f"- {a}: {m:+d}")
        if len(lines) == 1:
            lines.append("- None")

        lines.append("\nCaps (key):")
        for a in key:
            lines.append(f"- {a}: {caps.get(a, 95)}")

        lines.append("\nCost bias (key):")
        for a in ["Three-Point", "Ball Control", "Speed", "Agility", "Block", "Interior Defence"]:
            lines.append(f"- {a}: {cost.get(a, '-')}")
        return "\n".join(lines)

    def _refresh(self) -> None:
        self.update_top()
        self.query_one("#vitals", Static).update(self._vitals_text())
        self.query_one("#preview", Static).update(self._preview_text())

        self.query_one("#height-value", Label).update(self.state.physicals.height_str())
        self.query_one("#weight-value", Label).update(f"{self.state.physicals.weight_lb} lbs")
        self.query_one("#wingspan-value", Label).update(self.state.physicals.wingspan_str())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "back":
            self.app.pop_screen()
            return
        if bid == "next":
            self.app.push_screen("potential_preview")
            return

        if bid == "height-minus":
            self._adjust_height(-1)
        elif bid == "height-plus":
            self._adjust_height(+1)
        elif bid == "weight-minus":
            self._adjust_weight(-5)
        elif bid == "weight-plus":
            self._adjust_weight(+5)
        elif bid == "wingspan-minus":
            self._adjust_wingspan(-1)
        elif bid == "wingspan-plus":
            self._adjust_wingspan(+1)

    def _adjust_height(self, delta: int) -> None:
        pos = self.state.basic.position
        lo, hi = {
            "PG": (70, 78),
            "SG": (72, 81),
            "SF": (75, 84),
            "PF": (78, 86),
            "C": (80, 90),
        }[pos]
        self.state.physicals.height_in = clamp(self.state.physicals.height_in + delta, lo, hi)

        ws_lo = self.state.physicals.height_in + 0
        ws_hi = self.state.physicals.height_in + 8
        self.state.physicals.wingspan_in = clamp(self.state.physicals.wingspan_in, ws_lo, ws_hi)

        self._refresh()

    def _adjust_weight(self, delta: int) -> None:
        pos = self.state.basic.position
        lo, hi = {
            "PG": (160, 220),
            "SG": (170, 235),
            "SF": (185, 250),
            "PF": (210, 280),
            "C": (225, 310),
        }[pos]
        self.state.physicals.weight_lb = clamp(self.state.physicals.weight_lb + delta, lo, hi)
        self._refresh()

    def _adjust_wingspan(self, delta: int) -> None:
        ws_lo = self.state.physicals.height_in + 0
        ws_hi = self.state.physicals.height_in + 8
        self.state.physicals.wingspan_in = clamp(self.state.physicals.wingspan_in + delta, ws_lo, ws_hi)
        self._refresh()


class PotentialPreviewScreen(BaseWizardScreen):
    def compose_page(self) -> ComposeResult:
        yield Label("3A) Attribute Potential Preview (Caps)", classes="title")
        yield Label("Preview ceilings only. No spending here.", classes="subtitle")
        yield Rule()
        with Horizontal(classes="cols"):
            with Vertical(classes="col"):
                yield Static(self._vitals_card(), classes="panel", id="vitals_card")
                yield Rule()
                yield Static(self._cost_card(), classes="panel", id="cost_card")
            caps_sv = ScrollView(classes="col caps-scroll")
            try:
                if hasattr(caps_sv, "vertical_scrollbar") and caps_sv.vertical_scrollbar:
                    caps_sv.vertical_scrollbar.auto_hide = False  # type: ignore[attr-defined]
            except Exception:
                pass
            with caps_sv:
                yield Static(self._caps_text(), id="caps_text", classes="panel")
            yield caps_sv
        yield Rule()
        with Horizontal(classes="actions"):
            yield Button("Back", id="back")
            yield Button("Continue", id="next", variant="primary")

    def _vitals_card(self) -> str:
        b = self.state.basic
        p = self.state.physicals
        return (
            "Player\n"
            "------\n"
            f"{b.full_name}\n"
            f"{b.position} | {p.height_str()} | {p.weight_lb} lbs | {p.wingspan_str()}\n"
            f"Body: {self.state.body_label}\n"
        )

    def _cost_card(self) -> str:
        _, _, cost = compute_modifiers_and_caps(self.state)
        focus = ["Ball Control", "Three-Point", "Block", "Interior Defence", "Speed", "Agility"]
        lines = ["Cost bias (preview)\n-------"]
        for a in focus:
            lines.append(f"{a}: {cost.get(a, '-')}")
        return "\n".join(lines)

    def _caps_text(self) -> str:
        _, caps, _ = compute_modifiers_and_caps(self.state)
        lines: List[str] = []
        lines.append("ATTRIBUTE POTENTIAL (Ceilings)")
        lines.append("-----------------------------")
        for group, attrs in ATTRIBUTE_GROUPS:
            lines.append(f"\n{group.upper()}")
            lines.append("-----------------------------")
            for a in attrs:
                c = caps.get(a, 95)
                lines.append(f"{a:<18} {bar(c, 99, 16)}  Cap {c}")
        return "\n".join(lines)

    def _refresh(self) -> None:
        self.update_top()
        self.query_one("#vitals_card", Static).update(self._vitals_card())
        self.query_one("#cost_card", Static).update(self._cost_card())
        self.query_one("#caps_text", Static).update(self._caps_text())

    def on_screen_resume(self) -> None:
        self._refresh()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "next":
            self.app.push_screen("builder")


class AttributeBuilderScreen(BaseWizardScreen):
    """
    3B) Attribute Builder (spend points towards potential build).
    Now with soft-cap costs, physical bias, and arrow-key attribute hopping.
    """
    def compose_page(self) -> ComposeResult:
        yield Label("3B) Attribute Builder - Potential (Target: 99 OVR)", classes="title")
        yield Label("Spend points towards your 99 build. Career will scale this down at the start.", classes="subtitle")
        yield Rule()
        with Horizontal(classes="cols"):
            with Vertical(classes="col"):
                yield Static(self._left_card(), id="left_card", classes="panel")
                yield Rule()
                yield Label("Select attribute")
                yield Select([(a, a) for a in ALL_ATTRIBUTES], value="Layup", id="attr_select")
                with Horizontal(classes="actions"):
                    yield Button("-1", id="minus")
                    yield Button("+1", id="plus", variant="primary")
                    yield Button("Reset build", id="reset")
                yield Rule()
                yield Static(self._selected_detail("Layup"), id="detail", classes="panel")
            builder_sv = ScrollView(classes="col builder-scroll")
            try:
                if hasattr(builder_sv, "vertical_scrollbar") and builder_sv.vertical_scrollbar:
                    builder_sv.vertical_scrollbar.auto_hide = False  # type: ignore[attr-defined]
            except Exception:
                pass
            with builder_sv:
                yield Static(self._builder_text(), id="builder_text", classes="panel")
            yield builder_sv
            with Vertical(classes="col"):
                yield Static(self._summary_card(), id="summary_card", classes="panel")
                yield Rule()
                yield Button("Continue", id="next", variant="primary")
                yield Button("Back", id="back")

    def _left_card(self) -> str:
        b = self.state.basic
        p = self.state.physicals
        ovr = compute_public_ovr_from_potential(self.state)
        return (
            "Vitals\n------\n"
            f"{b.full_name}\n"
            f"{b.position} | {p.height_str()} | {p.weight_lb} lbs | {p.wingspan_str()}\n"
            f"Body: {self.state.body_label}\n\n"
            f"Budget: {self.state.budget_used}/{self.state.budget_total}\n"
            f"OVR (potential): {ovr} / 99\n"
        )

    def _summary_card(self) -> str:
        self.state.recalc()
        ovr = compute_public_ovr_from_potential(self.state)
        roles = ", ".join(self.state.roles) if self.state.roles else "-"
        return (
            "Build Summary\n------------\n"
            f"Build: {self.state.build_name}\n"
            f"Archetype: {self.state.archetype}\n"
            f"OVR (potential): {ovr}\n"
            f"Roles: {roles}\n"
            f"Budget: {self.state.budget_used}/{self.state.budget_total}\n"
        )

    def _builder_text(self) -> str:
        mods, caps, _ = compute_modifiers_and_caps(self.state)

        lines: List[str] = []
        lines.append("ATTRIBUTES (Potential values you are building)")
        lines.append("--------------------------------------------")
        for group, attrs in ATTRIBUTE_GROUPS:
            lines.append(f"\n{group.upper()}")
            lines.append("--------------------------------------------")
            for a in attrs:
                base = self.state.potential[a]
                cap = caps.get(a, 95)
                m = mods.get(a, 0)
                final = clamp(base + m, 25, 99)
                lines.append(
                    f"{a:<18} {bar(base, cap, 14)}  {base:>2} {fmt_mod(m):>5} -> {final:>2}   /{cap}"
                )
        return "\n".join(lines)

    def _selected_detail(self, attr: str) -> str:
        mods, caps, cost_bias = compute_modifiers_and_caps(self.state)
        base = self.state.potential[attr]
        cap = caps.get(attr, 95)
        m = mods.get(attr, 0)
        final = clamp(base + m, 25, 99)
        next_cost = point_cost_for_value(attr, base + 1, cost_bias) if base < cap else 0
        soft_note = ""
        if base >= SOFT_CAP_TIERS[1]:
            soft_note = "Tier: 90+ (max cost)"
        elif base >= SOFT_CAP_TIERS[0]:
            soft_note = "Tier: 80s (higher cost)"
        else:
            soft_note = "Tier: 60-70s (cheap)"
        bias = cost_bias.get(attr, "-")
        return (
            f"{attr}\n------\n"
            f"Potential: {base} / {cap}\n"
            f"Modifier: {m:+d}\n"
            f"Final in-game (at potential): {final}\n"
            f"Next point cost: {next_cost} (bias {bias})\n"
            f"{soft_note}\n\n"
            "Tip: You are building the ceiling.\n"
            "Career start will scale this down to ~60 OVR."
        )

    def _refresh(self) -> None:
        self.update_top()
        self.query_one("#left_card", Static).update(self._left_card())
        self.query_one("#builder_text", Static).update(self._builder_text())
        self.query_one("#summary_card", Static).update(self._summary_card())

        sel = self.query_one("#attr_select", Select).value or "Layup"
        self.query_one("#detail", Static).update(self._selected_detail(sel))

    def on_screen_resume(self) -> None:
        self._refresh()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "attr_select":
            self.query_one("#detail", Static).update(self._selected_detail(event.value))

    def on_key(self, event: events.Key) -> None:
        """Arrow keys jump attributes (Up/Down) and spend (Left/->) just like 2K."""
        select = self.query_one("#attr_select", Select)
        values = [opt[1] for opt in select.options] if hasattr(select, "options") else [a for a in ALL_ATTRIBUTES]
        if not values:
            return
        current = select.value or values[0]
        if event.key in ("up", "down"):
            step = -1 if event.key == "up" else 1
            idx = values.index(current) if current in values else 0
            new_idx = (idx + step) % len(values)
            select.value = values[new_idx]
            self.query_one("#detail", Static).update(self._selected_detail(select.value))
            event.stop()
        elif event.key in ("left", "right"):
            delta = -1 if event.key == "left" else 1
            self._spend(current, delta)
            event.stop()

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

    def _spend(self, attr: str, delta: int) -> None:
        mods, caps, cost_bias = compute_modifiers_and_caps(self.state)
        cap = caps.get(attr, 95)

        new_val = clamp(self.state.potential[attr] + delta, 25, cap)
        if new_val == self.state.potential[attr]:
            return

        candidate_potential = dict(self.state.potential)
        candidate_potential[attr] = new_val

        budget_total = caps_budget_total(caps, cost_bias, base=BUDGET_BASE)
        budget_used = total_cost_for_build(candidate_potential, cost_bias, base=BUDGET_BASE)
        if budget_used > budget_total:
            return

        self.state.potential = candidate_potential
        self.state.budget_total = budget_total
        self.state.budget_used = budget_used
        self._refresh()


class TendenciesAndDNAScreen(BaseWizardScreen):
    """
    4) Tendencies & DNA
    Minimal complete screen:
      - Adjust key tendency splits and keep them normalised
      - Adjust DNA sliders (0-100)
    """
    def compose_page(self) -> ComposeResult:
        yield Label("4) Tendencies & DNA", classes="title")
        yield Label("These shape behaviour in the sim. They do not change OVR directly.", classes="subtitle")
        yield Rule()

        with Horizontal(classes="cols"):
            with Vertical(classes="col"):
                yield Static(self._tendencies_card(), id="tend_card", classes="panel")
                yield Rule()
                yield Static(self._dna_card(), id="dna_card", classes="panel")
            with Vertical(classes="col"):
                yield Label("Quick edits (simple steppers)")
                yield Label("Shot Profile (Close / Mid / Three) - sums to 100")
                yield MiniValueStepper("Close", str(self.state.shot_profile_close), id="sp_close")
                yield MiniValueStepper("Mid", str(self.state.shot_profile_mid), id="sp_mid")
                yield MiniValueStepper("Three", str(self.state.shot_profile_three), id="sp_three")

                yield Rule()
                yield Label("Rim Attack (Layup / Dunk) - sums to 100")
                yield MiniValueStepper("Layup", str(self.state.rim_attack_layup), id="ra_lay")
                yield MiniValueStepper("Dunk", str(self.state.rim_attack_dunk), id="ra_dunk")

                yield Rule()
                yield Label("DNA (0-100)")
                yield MiniValueStepper("Risk", str(self.state.dna_risk), id="dna_risk")
                yield MiniValueStepper("Tempo", str(self.state.dna_tempo), id="dna_tempo")
                yield MiniValueStepper("Physicality", str(self.state.dna_physicality), id="dna_phys")
                yield MiniValueStepper("Streakiness", str(self.state.dna_streakiness), id="dna_streak")
                yield MiniValueStepper("Discipline", str(self.state.dna_discipline), id="dna_disc")

            with Vertical(classes="col"):
                yield Static(self._build_summary(), id="build_card", classes="panel")
                yield Rule()
                yield Button("Continue", id="next", variant="primary")
                yield Button("Back", id="back")

    def _tendencies_card(self) -> str:
        a, b, c = normalise3(self.state.shot_profile_close, self.state.shot_profile_mid, self.state.shot_profile_three)
        self.state.shot_profile_close, self.state.shot_profile_mid, self.state.shot_profile_three = a, b, c

        total = max(1, self.state.rim_attack_layup + self.state.rim_attack_dunk)
        self.state.rim_attack_layup = int(round(self.state.rim_attack_layup * 100 / total))
        self.state.rim_attack_dunk = 100 - self.state.rim_attack_layup

        return (
            "Tendencies\n----------\n"
            f"Shot profile: Close {self.state.shot_profile_close}% | Mid {self.state.shot_profile_mid}% | Three {self.state.shot_profile_three}%\n"
            f"Rim attack: Layup {self.state.rim_attack_layup}% | Dunk {self.state.rim_attack_dunk}%\n"
        )

    def _dna_card(self) -> str:
        return (
            "DNA (intent, not fate)\n--------------------\n"
            f"Risk: {self.state.dna_risk}\n"
            f"Tempo: {self.state.dna_tempo}\n"
            f"Physicality: {self.state.dna_physicality}\n"
            f"Streakiness: {self.state.dna_streakiness}\n"
            f"Discipline: {self.state.dna_discipline}\n"
        )

    def _build_summary(self) -> str:
        self.state.recalc()
        return (
            "Build Snapshot\n------------\n"
            f"Build: {self.state.build_name}\n"
            f"Body: {self.state.body_label}\n"
            f"Roles: {', '.join(self.state.roles) if self.state.roles else '-'}\n"
        )

    def _refresh(self) -> None:
        self.update_top()
        self.query_one("#tend_card", Static).update(self._tendencies_card())
        self.query_one("#dna_card", Static).update(self._dna_card())
        self.query_one("#build_card", Static).update(self._build_summary())

        self.query_one("#sp_close-value", Label).update(str(self.state.shot_profile_close))
        self.query_one("#sp_mid-value", Label).update(str(self.state.shot_profile_mid))
        self.query_one("#sp_three-value", Label).update(str(self.state.shot_profile_three))
        self.query_one("#ra_lay-value", Label).update(str(self.state.rim_attack_layup))
        self.query_one("#ra_dunk-value", Label).update(str(self.state.rim_attack_dunk))

        self.query_one("#dna_risk-value", Label).update(str(self.state.dna_risk))
        self.query_one("#dna_tempo-value", Label).update(str(self.state.dna_tempo))
        self.query_one("#dna_phys-value", Label).update(str(self.state.dna_physicality))
        self.query_one("#dna_streak-value", Label).update(str(self.state.dna_streakiness))
        self.query_one("#dna_disc-value", Label).update(str(self.state.dna_discipline))

    def on_screen_resume(self) -> None:
        self._refresh()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "back":
            self.app.pop_screen()
            return
        if bid == "next":
            self.app.push_screen("scouting")
            return

        def inc(v: int, d: int, lo: int = 0, hi: int = 100) -> int:
            return clamp(v + d, lo, hi)

        if bid == "sp_close-minus":
            self.state.shot_profile_close = inc(self.state.shot_profile_close, -1, 0, 100)
        elif bid == "sp_close-plus":
            self.state.shot_profile_close = inc(self.state.shot_profile_close, +1, 0, 100)
        elif bid == "sp_mid-minus":
            self.state.shot_profile_mid = inc(self.state.shot_profile_mid, -1, 0, 100)
        elif bid == "sp_mid-plus":
            self.state.shot_profile_mid = inc(self.state.shot_profile_mid, +1, 0, 100)
        elif bid == "sp_three-minus":
            self.state.shot_profile_three = inc(self.state.shot_profile_three, -1, 0, 100)
        elif bid == "sp_three-plus":
            self.state.shot_profile_three = inc(self.state.shot_profile_three, +1, 0, 100)

        elif bid == "ra_lay-minus":
            self.state.rim_attack_layup = inc(self.state.rim_attack_layup, -1, 0, 100)
        elif bid == "ra_lay-plus":
            self.state.rim_attack_layup = inc(self.state.rim_attack_layup, +1, 0, 100)
        elif bid == "ra_dunk-minus":
            self.state.rim_attack_dunk = inc(self.state.rim_attack_dunk, -1, 0, 100)
        elif bid == "ra_dunk-plus":
            self.state.rim_attack_dunk = inc(self.state.rim_attack_dunk, +1, 0, 100)

        elif bid == "dna_risk-minus":
            self.state.dna_risk = inc(self.state.dna_risk, -1)
        elif bid == "dna_risk-plus":
            self.state.dna_risk = inc(self.state.dna_risk, +1)
        elif bid == "dna_tempo-minus":
            self.state.dna_tempo = inc(self.state.dna_tempo, -1)
        elif bid == "dna_tempo-plus":
            self.state.dna_tempo = inc(self.state.dna_tempo, +1)
        elif bid == "dna_phys-minus":
            self.state.dna_physicality = inc(self.state.dna_physicality, -1)
        elif bid == "dna_phys-plus":
            self.state.dna_physicality = inc(self.state.dna_physicality, +1)
        elif bid == "dna_streak-minus":
            self.state.dna_streakiness = inc(self.state.dna_streakiness, -1)
        elif bid == "dna_streak-plus":
            self.state.dna_streakiness = inc(self.state.dna_streakiness, +1)
        elif bid == "dna_disc-minus":
            self.state.dna_discipline = inc(self.state.dna_discipline, -1)
        elif bid == "dna_disc-plus":
            self.state.dna_discipline = inc(self.state.dna_discipline, +1)

        self._refresh()


class FinalScoutingReportScreen(BaseWizardScreen):
    def compose_page(self) -> ComposeResult:
        yield Label("5) Final Scouting Report", classes="title")
        yield Label("This is how the world will see the player.", classes="subtitle")
        yield Rule()
        with Horizontal(classes="cols"):
            with Vertical(classes="col"):
                yield Static(self._report_text(), id="report", classes="panel")
            with Vertical(classes="col"):
                yield Static(self._attributes_compare(), id="compare", classes="panel")
                yield Rule()
                yield Button("Confirm & Start Career", id="next", variant="primary")
                yield Button("Back", id="back")

    def _report_text(self) -> str:
        self.state.recalc()
        b = self.state.basic
        p = self.state.physicals
        pot_ovr = compute_public_ovr_from_potential(self.state)

        sorted_attrs = sorted(ALL_ATTRIBUTES, key=lambda a: self.state.potential[a], reverse=True)
        strengths = sorted_attrs[:3]
        weaknesses = sorted_attrs[-3:]

        return (
            f"{b.full_name}\n"
            f"------------------------\n"
            f"Position: {b.position} | Hand: {b.hand}\n"
            f"Vitals: {p.height_str()} | {p.weight_lb} lbs | {p.wingspan_str()}\n"
            f"Hometown: {b.hometown} | Region: {b.region}\n\n"
            f"Build: {self.state.build_name}\n"
            f"Archetype: {self.state.archetype}\n"
            f"Potential OVR: {pot_ovr}\n"
            f"Budget Used: {self.state.budget_used}/{self.state.budget_total}\n\n"
            f"Tendencies:\n"
            f"- Shot profile: Close {self.state.shot_profile_close}% / Mid {self.state.shot_profile_mid}% / Three {self.state.shot_profile_three}%\n"
            f"- Rim attack: Layup {self.state.rim_attack_layup}% / Dunk {self.state.rim_attack_dunk}%\n\n"
            f"Projected roles: {', '.join(self.state.roles) if self.state.roles else '-'}\n\n"
            f"Strengths:\n"
            f"- {strengths[0]}\n- {strengths[1]}\n- {strengths[2]}\n\n"
            f"Weaknesses:\n"
            f"- {weaknesses[0]}\n- {weaknesses[1]}\n- {weaknesses[2]}\n"
        )

    def _attributes_compare(self) -> str:
        mods, caps, _ = compute_modifiers_and_caps(self.state)
        current = compute_starting_scaled_attributes(self.state, target_start_ovr=60)
        pot_ovr = compute_public_ovr_from_potential(self.state)

        key = ["Three-Point", "Ball Control", "Perimeter Defence", "Block", "Speed", "Strength", "Offensive IQ", "Defensive IQ"]
        lines = []
        lines.append("Potential vs Career Start")
        lines.append("------------------------")
        lines.append(f"Potential OVR: {pot_ovr} -> Career start: ~60")
        lines.append("")
        for a in key:
            pot = self.state.potential[a]
            m = mods.get(a, 0)
            final_pot = clamp(pot + m, 25, 99)
            start = current.get(a, 50)
            lines.append(f"{a:<18} Pot {final_pot:>2}   Start {start:>2}   Cap {caps.get(a, 95)}")
        lines.append("\nNote: Career start values are scaled down.\nProgression moves towards the potential build.")
        return "\n".join(lines)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "next":
            self.app.push_screen("confirm")


class ConfirmStartScreen(BaseWizardScreen):
    def compose_page(self) -> ComposeResult:
        yield Label("6) Confirm & Start Career", classes="title")
        yield Label("This will create the career-start attributes (~60 OVR) from your 99 potential build.", classes="subtitle")
        yield Rule()
        with Horizontal(classes="cols"):
            with Vertical(classes="col"):
                yield Static(self._final_card(), id="final", classes="panel")
            with Vertical(classes="col"):
                yield Button("Start Career (save data)", id="start", variant="primary")
                yield Button("Back", id="back")
                yield Rule()
                yield Static("Tip: This demo prints a JSON-like summary to the terminal log.\nYou can wire this into SQLite later.", classes="panel")

    def _final_card(self) -> str:
        b = self.state.basic
        p = self.state.physicals
        pot_ovr = compute_public_ovr_from_potential(self.state)
        current = compute_starting_scaled_attributes(self.state, target_start_ovr=60)

        key = ["Layup", "Dunk", "Three-Point", "Ball Control", "Perimeter Defence", "Steal", "Block", "Speed", "Strength"]
        lines = [
            "Final Summary",
            "-------------",
            f"Name: {b.full_name}",
            f"Position: {b.position}",
            f"Vitals: {p.height_str()} | {p.weight_lb} lbs | {p.wingspan_str()}",
            f"Build: {self.state.build_name}",
            f"Potential OVR: {pot_ovr}",
            "Career start (sample):",
        ]
        for a in key:
            lines.append(f"- {a}: {current.get(a, 50)}")
        return "\n".join(lines)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "start":
            b = self.state.basic
            p = self.state.physicals
            pot = dict(self.state.potential)
            current = compute_starting_scaled_attributes(self.state, target_start_ovr=60)
            payload = {
                "basic": b.__dict__,
                "physicals": {"height_in": p.height_in, "weight_lb": p.weight_lb, "wingspan_in": p.wingspan_in},
                "body_label": self.state.body_label,
                "build_name": self.state.build_name,
                "archetype": self.state.archetype,
                "roles": self.state.roles,
                "potential_attributes": pot,
                "career_start_attributes": current,
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

class CharacterCreatorApp(App):
    CSS = """
    Screen {
        background: #0b0f14;
        color: #e8eef7;
    }
    #scroll_root {
        height: 1fr;
        width: 100%;
        overflow-y: auto;
        scrollbar-gutter: stable;
    }
    #page, .page {
        padding: 0 1;
        width: 100%;
        height: auto;
    }
    ScrollView, .caps-scroll, .builder-scroll {
        scrollbar-gutter: stable;
        overflow-y: auto;
    }
    .caps-scroll {
        height: 24;
        width: 100%;
    }
    .builder-scroll {
        height: 28;
        width: 100%;
    }
    .title {
        text-style: bold;
    }
    .subtitle {
        color: #a9b7c6;
    }
    .cols {
        height: 1fr;
        width: 100%;
    }
    .col {
        width: 1fr;
        min-width: 16;
        padding: 0 1 0 0;
        max-width: 100%;
    }
    .panel {
        border: round #2b3a4a;
        padding: 1 1;
        background: #0f1621;
        width: 100%;
    }
    .actions {
        padding-top: 1;
    }
    .stepper {
        height: auto;
        margin: 0 0 1 0;
    }
    .stepper-title {
        width: 10;
        color: #c9d6e2;
    }
    .stepper-value {
        width: 8;
        text-style: bold;
    }
    .stepper-btn {
        width: 4;
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
    CharacterCreatorApp().run()


