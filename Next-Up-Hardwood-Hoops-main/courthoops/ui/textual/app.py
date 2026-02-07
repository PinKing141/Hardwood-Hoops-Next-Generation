from __future__ import annotations

import json
from typing import Dict, List

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Header, Footer, Input, Select, Static, TabbedContent, TabPane, Button
try:  # Textual Slider may be missing in older versions
    from textual.widgets import Slider  # type: ignore
except Exception:  # pragma: no cover
    from courthoops.ui.textual.slider import Slider  # type: ignore

from courthoops.domain.player.entity import Player, PlayerAttributes, PlayerPersonality, PlayerTendencies
from courthoops.app.services.build_name_service import BuildNameService
from courthoops.app.services.scouting_service import ScoutingService
from courthoops.ui.textual.physical_modifiers import COST_DOWN, COST_UP, ModifierPreview, compute_modifiers, cost_arrows_by_attribute
from courthoops.infra.generators.city_service import CityService
from courthoops.infra.persistence.orm.session import make_session_factory
from courthoops.infra.utils.config import AppConfig
from courthoops.ui.textual.confirm_screen import ConfirmScreen
from courthoops.infra.utils.rng import PythonRNG
import importlib
from typing import Any


class CharacterCreatorApp(App):
    """Textual UI for the character creator (Vitals -> Attributes/Tendencies/DNA -> Build preview)."""

    CSS_PATH = None
    TITLE = "Courthoops Character Creator"
    BASE_ATTR_CAP = 95
    MIN_EFFECTIVE_ATTR = 25
    PHASES = ["identity", "body", "potential", "builder", "tendencies", "report"]
    ATTR_GROUPS = {
        "Finishing": ["layup", "dunk", "inside"],
        "Shooting": ["mid_range", "three_point", "free_throw"],
        "Playmaking": ["ball_control", "passing"],
        "Defense": ["perimeter_defense", "interior_defense", "steal", "block"],
        "Rebounding": ["offensive_rebound", "defensive_rebound"],
        "Athleticism": ["speed", "agility", "vertical", "strength", "stamina"],
        "Mental & IQ": ["offensive_iq", "defensive_iq", "hustle"],
    }

    first_name = reactive("New")
    last_name = reactive("Player")
    name = reactive("New Player")
    position = reactive("SG")
    height = reactive(76)
    weight = reactive(195)
    wingspan = reactive(79)
    hometown = reactive("")
    month = reactive("January")
    day = reactive("1")
    export_path = reactive("player_build.json")

    attr_values: Dict[str, int] = reactive({})
    tendency_values: Dict[str, int] = reactive({})
    personality_work = reactive(50)
    personality_coach = reactive(50)
    personality_compete = reactive(50)
    hidden_potential = reactive(80)
    hidden_injury = reactive(50)
    hidden_clutch = reactive(60)
    hidden_consistency = reactive(65)
    hidden_discipline = reactive(65)
    minutes_allocation = reactive(20)
    budget_spent = reactive(0)
    personality_rolls = reactive(3)
    phase_idx = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.city_service = CityService("courthoops/data/us-cities.db", PythonRNG(seed=1))
        self.city_options = self._city_options()
        self.build_namer = BuildNameService()
        self.scouting = ScoutingService()
        self.budget_cap = 800  # rough budget limit
        self._tabs = None
        self._tabs_populated = False
        # Repo wiring (optional; tolerate missing DB models)
        cfg = AppConfig()
        self.player_repo = None
        try:
            models = importlib.import_module("courthoops.infra.persistence.orm.models")
            repo_mod = importlib.import_module("courthoops.infra.persistence.repositories.player_repository")
            base = getattr(models, "Base", None)
            player_repo_cls: Any = getattr(repo_mod, "PlayerRepository", None)
            if base and player_repo_cls:
                session_factory = make_session_factory(cfg.database_url, base.metadata)
                self.player_repo = player_repo_cls(session_factory, universe_id=cfg.universe_id if hasattr(cfg, "universe_id") else "UNIVERSE")
        except Exception as exc:  # pragma: no cover - offline / schema failures
            self.console.log(f"DB unavailable for player saving: {exc}")

    def compose(self) -> ComposeResult:
        self._init_defaults()
        yield Header()
        with Horizontal():
            # Left column: Identity + Body (always accessible)
            with Vertical(id="form-panel"):
                yield Static("PLAYER INFO", classes="section-title")
                yield Input(placeholder="First Name", value=self.first_name, id="first-name-input")
                yield Input(placeholder="Last Name", value=self.last_name, id="last-name-input")
                yield Select(options=[("PG", "PG"), ("SG", "SG"), ("SF", "SF"), ("PF", "PF"), ("C", "C")], value=self.position, id="pos-select")
                yield Static("Height / Weight / Wingspan", classes="section-title")
                yield Slider(id="height-slider", name="Height (in)", value=self.height, minimum=72, maximum=86, step=1)
                yield Slider(id="weight-slider", name="Weight (lb)", value=self.weight, minimum=160, maximum=280, step=1)
                yield Slider(id="wingspan-slider", name="Wingspan (in)", value=self.wingspan, minimum=72, maximum=90, step=1)
                yield Select(options=self._month_options(), value=self.month, id="month-select")
                yield Input(placeholder="Day", value=self.day, id="day-input")
                yield Select(options=self.city_options, value=self.city_options[0][1] if self.city_options else "", id="city-select")
                yield Button("Randomise Body", id="random-body")
                yield Button("Reset Body", id="reset-body")
                self.error_view = Static("", classes="error")
                yield self.error_view

            # Center column: staged content (potential preview, builder, tendencies)
            with Vertical(id="attr-panel"):
                self.phase_header = Static("", id="phase-header")
                yield self.phase_header
                self.attr_preview = Static("", id="attr-preview")
                yield self.attr_preview
                # Attribute builder controls (only shown during builder/tendency phases)
                self._tabs = TabbedContent()
                yield self._tabs
                yield Button("Continue", id="continue", disabled=False)

            # Right column: vitals + build summary + budget/warnings
            with Vertical(id="summary-panel"):
                self.vitals_preview = Static("", id="vitals-preview")
                self.build_preview = Static("", id="build-preview")
                self.budget_preview = Static("", id="budget-preview")
                self.tendency_warning = Static("", id="tendency-warning")

                yield self.vitals_preview
                yield self.build_preview
                yield self.budget_preview
                yield self.tendency_warning

        yield Footer()

    def _attributes_tab(self) -> Static:
        widgets = [Static("Attributes (Base)", classes="section-title")]
        for attr, label in self._attribute_fields().items():
            widgets.append(Slider(id=f"attr-{attr}", name=label, value=self.attr_values[attr], minimum=40, maximum=95, step=1))
            widgets.append(Static("", id=f"cost-{attr}", classes="hint"))
        return Vertical(*widgets)

    def _tendencies_tab(self) -> Static:
        widgets = [Static("Tendencies (normalised later)", classes="section-title")]
        for key, label in self._tendency_fields().items():
            widgets.append(Slider(id=f"tendency-{key}", name=label, value=self.tendency_values[key], minimum=0, maximum=100, step=1))
        return Vertical(*widgets)

    def _dna_tab(self) -> Static:
        widgets = [
            Static("Personality", classes="section-title"),
            Slider(id="personality-work", name="Work Ethic", value=self.personality_work, minimum=0, maximum=100, step=1),
            Slider(id="personality-coach", name="Coachability", value=self.personality_coach, minimum=0, maximum=100, step=1),
            Slider(id="personality-compete", name="Competitiveness", value=self.personality_compete, minimum=0, maximum=100, step=1),
            Button(f"Roll Personality ({self.personality_rolls})", id="roll-personality"),
            Static("Minutes Allocation", classes="section-title"),
            Slider(id="minutes-allocation", name="Minutes", value=self.minutes_allocation, minimum=5, maximum=40, step=1),
            Static("Hidden Attributes", classes="section-title"),
            Slider(id="hidden-potential", name="Potential", value=self.hidden_potential, minimum=40, maximum=99, step=1),
            Slider(id="hidden-injury", name="Injury Proneness", value=self.hidden_injury, minimum=25, maximum=95, step=1),
            Slider(id="hidden-clutch", name="Clutch", value=self.hidden_clutch, minimum=30, maximum=95, step=1),
            Slider(id="hidden-consistency", name="Consistency", value=self.hidden_consistency, minimum=30, maximum=95, step=1),
            Slider(id="hidden-discipline", name="Decision Discipline", value=self.hidden_discipline, minimum=35, maximum=95, step=1),
            Button("Normalise Tendencies", id="normalise-tendencies"),
        ]
        return Vertical(*widgets)

    def on_mount(self) -> None:
        self._ensure_tabs()
        self._apply_phase_visibility()
        self._refresh_preview()

    def _ensure_tabs(self) -> None:
        """Populate TabbedContent lazily for older Textual versions."""
        if self._tabs_populated or not self._tabs:
            return
        try:
            self._tabs.add_pane(TabPane("Attributes", self._attributes_tab(), id="tab-attr"))
            self._tabs.add_pane(TabPane("Tendencies", self._tendencies_tab(), id="tab-tend"))
            self._tabs.add_pane(TabPane("DNA", self._dna_tab(), id="tab-dna"))
            self._tabs_populated = True
        except Exception as exc:
            self.console.log(f"Failed to build tabs: {exc}")

    def _city_options(self) -> List[tuple[str, str]]:
        opts = []
        for city in self.city_service._cities[:25]:
            label = f"{city['city']}, {city['state_id']}"
            opts.append((label, label))
        return opts

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "random-body":
            import random

            self.height = random.randint(72, 86)
            self.weight = random.randint(170, 260)
            self.wingspan = random.randint(72, 90)
            self.query_one("#height-slider", Slider).value = self.height
            self.query_one("#weight-slider", Slider).value = self.weight
            self.query_one("#wingspan-slider", Slider).value = self.wingspan
            self._refresh_preview()
        elif event.button.id == "reset-body":
            self.height, self.weight, self.wingspan = 76, 195, 79
            self.query_one("#height-slider", Slider).value = self.height
            self.query_one("#weight-slider", Slider).value = self.weight
            self.query_one("#wingspan-slider", Slider).value = self.wingspan
            self._refresh_preview()
        elif event.button.id == "roll-personality" and self.personality_rolls > 0:
            rng = PythonRNG()
            self.personality_work = int(rng.random() * 100)
            self.personality_coach = int(rng.random() * 100)
            self.personality_compete = int(rng.random() * 100)
            self.personality_rolls -= 1
            self.query_one("#personality-work", Slider).value = self.personality_work
            self.query_one("#personality-coach", Slider).value = self.personality_coach
            self.query_one("#personality-compete", Slider).value = self.personality_compete
            self._refresh_preview()
        elif event.button.id == "save-json":
            player = self._current_player()
            self._save_json(player)
        elif event.button.id == "continue":
            self._advance_phase()
        elif event.button.id == "normalise-tendencies":
            self._normalise_tendencies_inputs()
            self._refresh_preview()

    def on_key(self, event) -> None:  # type: ignore[override]
        """Let arrow keys move focus between widgets so mouse isn't required."""
        key = getattr(event, "key", "").lower()
        # Keep arrow keys on sliders for value changes; otherwise move focus
        if key in ("up", "left"):
            if not isinstance(self.focused, Slider):
                self._cycle_focus(forward=False)
                event.stop()
        elif key in ("down", "right"):
            if not isinstance(self.focused, Slider):
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

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "first-name-input":
            self.first_name = event.value
        if event.input.id == "last-name-input":
            self.last_name = event.value
        # Keep composite name in sync
        self.name = f"{self.first_name} {self.last_name}".strip()
        if event.input.id == "day-input":
            self.day = event.value
        self._refresh_preview()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "pos-select":
            self.position = event.value
        elif event.select.id == "month-select":
            self.month = event.value
        elif event.select.id == "city-select":
            self.hometown = event.value
        self._refresh_preview()

    def on_slider_changed(self, event: Slider.Changed) -> None:
        sid = event.slider.id
        if sid == "height-slider":
            self.height = int(event.value)
        elif sid == "weight-slider":
            self.weight = int(event.value)
        elif sid == "wingspan-slider":
            self.wingspan = int(event.value)
        elif sid and sid.startswith("attr-"):
            key = sid.replace("attr-", "")
            self.attr_values[key] = int(event.value)
        elif sid and sid.startswith("tendency-"):
            key = sid.replace("tendency-", "")
            self.tendency_values[key] = int(event.value)
        elif sid == "personality-work":
            self.personality_work = int(event.value)
        elif sid == "personality-coach":
            self.personality_coach = int(event.value)
        elif sid == "personality-compete":
            self.personality_compete = int(event.value)
        elif sid == "minutes-allocation":
            self.minutes_allocation = int(event.value)
        elif sid == "hidden-potential":
            self.hidden_potential = int(event.value)
        elif sid == "hidden-injury":
            self.hidden_injury = int(event.value)
        elif sid == "hidden-clutch":
            self.hidden_clutch = int(event.value)
        elif sid == "hidden-consistency":
            self.hidden_consistency = int(event.value)
        elif sid == "hidden-discipline":
            self.hidden_discipline = int(event.value)
        self._refresh_preview()

    def _advance_phase(self) -> None:
        # Last phase triggers confirmation/save
        if self.phase_idx >= len(self.PHASES) - 1:
            player = self._current_player()
            errors = self._validate(player)
            if errors:
                self.error_view.update("\n".join(errors))
                return
            self.error_view.update("")
            summary = self._summary_text(player)
            details = self._details_text(player)
            def on_close(result: bool | None) -> None:
                if result:
                    if self.player_repo:
                        try:
                            self.player_repo.save(player)
                            self.console.log(f"Saved player {player.player_id} to DB")
                        except Exception as e:
                            self.error_view.update(f"DB save failed: {e}. Saved JSON fallback.")
                            self._save_json(player)
                    else:
                        self.error_view.update("Repo not configured; saved JSON instead.")
                        self._save_json(player)
                self.pop_screen()

            save_enabled = bool(self.player_repo)
            if not save_enabled:
                self.error_view.update("Repo not configured; using JSON export.")
            self.push_screen(ConfirmScreen(summary, details=details, save_enabled=save_enabled), callback=on_close)
            return
        self.phase_idx = min(self.phase_idx + 1, len(self.PHASES) - 1)
        self._apply_phase_visibility()
        self._refresh_preview()

    def _apply_phase_visibility(self) -> None:
        phase = self.PHASES[self.phase_idx]
        # Hide tabbed controls unless in builder/tendencies
        if phase in ("builder", "tendencies"):
            self._tabs.display = True
        else:
            self._tabs.display = False

    def _current_player(self) -> Player:
        tendencies = self._normalized_tendencies()
        attrs = self._build_attributes()
        personality = PlayerPersonality(
            work_ethic=self.personality_work / 100.0,
            coachability=self.personality_coach / 100.0,
            competitiveness=self.personality_compete / 100.0,
        )
        city_meta = self._selected_city_meta()
        stats = {
            "position": self.position,
            "home_city": city_meta.get("city") if city_meta else self.hometown,
            "home_state": city_meta.get("state_id") if city_meta else "",
            "home_region": city_meta.get("region") if city_meta else "",
        }
        return Player(
            player_id="preview",
            name=self.name,
            class_year="College FR",
            attributes=attrs,
            tendencies=tendencies,
            personality=personality,
            stats=stats,
            minutes_allocation=self.minutes_allocation,
        )

    def _refresh_preview(self) -> None:
        preview = self._modifier_preview()
        player = self._current_player()
        name = self.build_namer.generate_name(player, position_map={player.player_id: self.position})
        report = self.scouting.scouting_reports([player], role_map={player.player_id: self.position})
        entry = report.get(player.player_id, {})
        vitals_lines = self._vitals_lines(preview)
        self.vitals_preview.update("\n".join(vitals_lines))
        arrows = cost_arrows_by_attribute(self.position, self.height, self.weight, self.wingspan)
        build_lines = self._summary_lines(name, entry, preview, arrows)
        self.build_preview.update("\n".join(build_lines))
        center_lines = self._center_phase_content(preview, name, entry, arrows)
        self.attr_preview.update("\n".join(center_lines))
        spent = self._compute_budget()
        # Hide budget label here; summary already shows it
        self.budget_preview.update("")
        # Disable continue when over budget
        cont_btn = self.query_one("#continue", Button)
        cont_btn.disabled = spent > self.budget_cap
        # Update cost hints per attribute using physical cost arrows
        for attr in self._attribute_fields().keys():
            hint_widget = self.query_one(f"#cost-{attr}", Static)
            phys_hint = arrows.get(attr, "")
            soft_hint = self._cost_hint(attr)
            hint_widget.update(f"{soft_hint} {phys_hint}".strip())
        # Suppress tendency warnings from the main view
        self.tendency_warning.update("")

    @staticmethod
    def _month_options() -> List[tuple[str, str]]:
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        return [(m, m) for m in months]

    def _attribute_fields(self) -> Dict[str, str]:
        return {
            "layup": "Layup",
            "dunk": "Dunk",
            "inside": "Inside",
            "mid_range": "Mid-Range",
            "three_point": "Three-Point",
            "free_throw": "Free Throw",
            "offensive_rebound": "Offensive Rebound",
            "ball_control": "Ball Control",
            "passing": "Passing",
            "defensive_rebound": "Defensive Rebound",
            "perimeter_defense": "Perimeter Defence",
            "interior_defense": "Interior Defence",
            "steal": "Steal",
            "block": "Block",
            "speed": "Speed",
            "agility": "Agility",
            "vertical": "Vertical",
            "strength": "Strength",
            "stamina": "Stamina",
            "offensive_iq": "Offensive IQ",
            "defensive_iq": "Defensive IQ",
            "hustle": "Hustle",
        }

    def _tendency_fields(self) -> Dict[str, str]:
        return {
            "shot_close": "Shot Profile: Close%",
            "shot_mid": "Shot Profile: Mid%",
            "shot_three": "Shot Profile: Three%",
            "rim_layup": "Rim: Layup%",
            "rim_dunk": "Rim: Dunk%",
            "creation_catch": "Creation: Catch%",
            "creation_pull": "Creation: Pull-Up%",
            "creation_drive": "Creation: Drive%",
            "play_score": "Playmaking Bias: Score%",
            "play_pass": "Playmaking Bias: Pass%",
            "def_disc": "Defence: Disciplined%",
            "def_gamble": "Defence: Gambler%",
            "help_help": "Help Defence: Help%",
            "help_home": "Help Defence: Stay Home%",
            "rebound_crash": "Rebound: Crash%",
            "rebound_run": "Rebound: Run%",
        }

    def _init_defaults(self) -> None:
        self.attr_values = {k: 60 for k in self._attribute_fields().keys()}
        self.tendency_values = {k: 50 for k in self._tendency_fields().keys()}

    def _modifier_preview(self) -> ModifierPreview:
        return compute_modifiers(self.position, self.height, self.weight, self.wingspan)

    def _attribute_effect(self, attr: str, preview: ModifierPreview) -> Dict[str, int]:
        base = self.attr_values.get(attr, 0)
        mod = preview.modifiers.get(attr, 0)
        cap_delta = preview.caps.get(attr, 0)
        cap = max(self.BASE_ATTR_CAP + cap_delta, 40)
        effective = max(self.MIN_EFFECTIVE_ATTR, min(base + mod, cap))
        return {"base": base, "mod": mod, "cap": cap, "effective": effective}

    def _effective_attributes(self, preview: ModifierPreview | None = None) -> Dict[str, int]:
        preview = preview or self._modifier_preview()
        return {k: self._attribute_effect(k, preview)["effective"] for k in self._attribute_fields().keys()}

    def _fmt_pairs(self, data: Dict[str, object], show_sign: bool = True) -> str:
        if not data:
            return "None"
        parts = []
        for k, v in data.items():
            if isinstance(v, int) and show_sign:
                parts.append(f"{k}:{v:+d}")
            else:
                parts.append(f"{k}:{v}")
        return ", ".join(parts)

    def _vitals_lines(self, preview: ModifierPreview) -> List[str]:
        meta = self._selected_city_meta()
        def _ft(inches: int) -> str:
            feet = inches // 12
            inch = inches % 12
            return f"{feet}'{inch}\""
        return [
            "PLAYER VITALS",
            "----------------------",
            f"Name       {self.name}",
            f"Position   {self.position}",
            f"Birth      {self.month} {self.day}",
            f"Hometown   {self.hometown or '—'}",
            f"Region     {meta.get('region', '')}",
            "",
            f"Height     {_ft(self.height)}",
            f"Weight     {self.weight} lbs",
            f"Wingspan   {_ft(self.wingspan)}",
            f"Body       {preview.proto_label}",
        ]

    def _summary_lines(self, build_name: str, entry: Dict[str, object], preview: ModifierPreview, arrows: Dict[str, str]) -> List[str]:
        strengths, weaknesses = self._strengths_weaknesses(preview)
        cost_bias = self._cost_bias(arrows)
        lines = [
            "BUILD SUMMARY",
            "----------------------",
            f"Build      {build_name}",
            f"Archetype  {preview.proto_label}",
            f"OVR        {entry.get('public_ovr', '?')}",
            f"Roles      {', '.join(entry.get('role_descriptors', [])) or '—'}",
        ]
        if strengths:
            lines.append("Strengths")
            lines.extend([f"• {s}" for s in strengths])
        if weaknesses:
            lines.append("Weaknesses")
            lines.extend([f"• {w}" for w in weaknesses])
        if cost_bias:
            lines.append("Cost Bias")
            lines.extend([f"• {c}" for c in cost_bias])
        return lines

    # Phase-driven center content
    def _center_phase_content(self, preview: ModifierPreview, build_name: str, entry: Dict[str, object], arrows: Dict[str, str]) -> List[str]:
        phase = self.PHASES[self.phase_idx]
        self.phase_header.update(f"Phase: {phase.title()}")
        if phase in ("identity", "body"):
            return ["Physical Profile Preview", "Caps & modifiers update live on the right."]
        if phase == "potential":
            return self._attribute_bar_lines(preview)
        if phase == "builder":
            # Show builder controls (tabs) and hide static preview
            self._tabs.display = True
            return ["Attribute Builder (use tabs below to edit)"]
        if phase == "tendencies":
            self._tabs.display = True
            self._tabs.active = "tab-tend"
            return ["Tendencies & DNA (tabs below)"]
        if phase == "report":
            lines = [
                "FINAL SCOUTING REPORT",
                "----------------------",
                f"Build      {build_name}",
                f"Archetype  {preview.proto_label}",
                f"Public OVR {entry.get('public_ovr', '?')}",
                "Strengths",
            ]
            strengths, weaknesses = self._strengths_weaknesses(preview)
            lines.extend([f"• {s}" for s in strengths] or ["• —"])
            lines.append("Weaknesses")
            lines.extend([f"• {w}" for w in weaknesses] or ["• —"])
            lines.append("Cost Bias")
            lines.extend([f"• {c}" for c in self._cost_bias(arrows)] or ["• —"])
            return lines
        return []

    def _strengths_weaknesses(self, preview: ModifierPreview) -> tuple[List[str], List[str]]:
        labels = self._attribute_fields()
        mods = preview.modifiers
        positives = sorted([(k, v) for k, v in mods.items() if v > 0], key=lambda kv: kv[1], reverse=True)[:3]
        negatives = sorted([(k, v) for k, v in mods.items() if v < 0], key=lambda kv: kv[1])[:3]
        strengths = [f"{labels.get(k, k)} {v:+d}" for k, v in positives]
        weaknesses = [f"{labels.get(k, k)} {v:+d}" for k, v in negatives]
        return strengths, weaknesses

    def _cost_bias(self, arrows: Dict[str, str]) -> List[str]:
        labels = self._attribute_fields()
        items = list(arrows.items())[:4]
        return [f"{labels.get(k, k)} {v}" for k, v in items]

    def _attribute_bar_lines(self, preview: ModifierPreview) -> List[str]:
        lines = ["ATTRIBUTE BUILDER — POTENTIAL (Target: 99 OVR)", "--------------------------------"]
        effects = {k: self._attribute_effect(k, preview) for k in self._attribute_fields().keys()}
        for group, keys in self.ATTR_GROUPS.items():
            lines.append(group.upper())
            lines.append("-" * 40)
            for key in keys:
                label = self._attribute_fields()[key]
                effect = effects[key]
                delta = effect["mod"]
                bar = self._bar(effect["effective"], effect["cap"])
                cap_note = " cap" if effect["effective"] != effect["base"] + delta else ""
                lines.append(f"{label:16} {bar} {effect['effective']:>2} ({delta:+d}) Max {effect['cap']}{cap_note}")
            lines.append("")
        return lines

    def _bar(self, value: int, cap: int, width: int = 22) -> str:
        capped = max(1, cap)
        clamped = max(0, min(capped, value))
        filled = int((clamped / capped) * width)
        filled_char = "█"
        empty_char = "░"
        return filled_char * filled + empty_char * (width - filled)

    def _build_attributes(self) -> PlayerAttributes:
        preview = self._modifier_preview()
        vals = self._effective_attributes(preview)
        return PlayerAttributes(
            layup=vals["layup"],
            dunk=vals["dunk"],
            inside=vals["inside"],
            mid_range=vals["mid_range"],
            three_point=vals["three_point"],
            free_throw=vals["free_throw"],
            offensive_rebound=vals["offensive_rebound"],
            ball_control=vals["ball_control"],
            passing=vals["passing"],
            defensive_rebound=vals["defensive_rebound"],
            perimeter_defense=vals["perimeter_defense"],
            interior_defense=vals["interior_defense"],
            steal=vals["steal"],
            block=vals["block"],
            speed=vals["speed"],
            agility=vals["agility"],
            vertical=vals["vertical"],
            strength=vals["strength"],
            stamina=vals["stamina"],
            offensive_iq=vals["offensive_iq"],
            defensive_iq=vals["defensive_iq"],
            hustle=vals["hustle"],
            potential=self.hidden_potential,
            injury_proneness=self.hidden_injury,
            clutch=self.hidden_clutch,
            consistency=self.hidden_consistency,
            decision_discipline=self.hidden_discipline,
        )

    def _normalized_tendencies(self) -> PlayerTendencies:
        t = self.tendency_values
        def norm(keys: List[str]) -> List[float]:
            total = sum(max(t[k], 0) for k in keys) or 1
            return [max(t[k], 0) / total for k in keys]

        return PlayerTendencies(
            shot_profile=norm(["shot_close", "shot_mid", "shot_three"]),
            rim_aggression=norm(["rim_layup", "rim_dunk"]),
            shot_creation=norm(["creation_catch", "creation_pull", "creation_drive"]),
            playmaking_bias=norm(["play_score", "play_pass", "creation_drive"]),
            pass_profile=[0.4, 0.3, 0.3],
            defensive_style=norm(["def_disc", "def_gamble", "def_disc"]),
            help_defense=norm(["help_help", "help_home", "help_help"]),
            rebound_bias=norm(["rebound_crash", "rebound_run", "rebound_crash"]),
            athletic_usage=[0.3, 0.3, 0.2, 0.2],
        )

    def _tendency_warning_text(self) -> str:
        """Return warning if any group is not normalised to ~100 before normalisation."""
        warn_parts = []
        def check(keys: List[str], label: str):
            total = sum(self.tendency_values[k] for k in keys)
            if total != 100:
                warn_parts.append(f"{label} totals {total} (will normalise).")
        check(["shot_close", "shot_mid", "shot_three"], "Shot Profile")
        check(["rim_layup", "rim_dunk"], "Rim Aggression")
        check(["creation_catch", "creation_pull", "creation_drive"], "Shot Creation")
        check(["play_score", "play_pass", "creation_drive"], "Playmaking Bias")
        check(["def_disc", "def_gamble", "def_disc"], "Defence Style")
        check(["help_help", "help_home", "help_help"], "Help Defence")
        check(["rebound_crash", "rebound_run", "rebound_crash"], "Rebound Bias")
        return "\n".join(warn_parts)

    def _normalise_tendencies_inputs(self) -> None:
        def norm_group(keys: List[str]):
            total = sum(self.tendency_values[k] for k in keys) or 1
            for k in keys:
                self.tendency_values[k] = int((self.tendency_values[k] / total) * 100)

        norm_group(["shot_close", "shot_mid", "shot_three"])
        norm_group(["rim_layup", "rim_dunk"])
        norm_group(["creation_catch", "creation_pull", "creation_drive"])
        norm_group(["play_score", "play_pass", "creation_drive"])
        norm_group(["def_disc", "def_gamble", "def_disc"])
        norm_group(["help_help", "help_home", "help_help"])
        norm_group(["rebound_crash", "rebound_run", "rebound_crash"])
        # Update sliders to reflect new values
        for key in self._tendency_fields().keys():
            slider = self.query_one(f"#tendency-{key}", Slider)
            slider.value = self.tendency_values[key]

    def _compute_budget(self) -> int:
        base = 50
        spend = 0
        for val in self.attr_values.values():
            delta = max(0, val - base)
            if val > 85:
                cost = delta * 3
            elif val > 70:
                cost = delta * 2
            else:
                cost = delta
            spend += cost
        self.budget_spent = spend
        return spend

    def _cost_hint(self, attr: str) -> str:
        # Simple soft-cap hints; tie into physical cost shifts
        hard_soft = {
            "ball_control": f"{COST_UP} past 80",
            "three_point": f"{COST_UP} past 80",
            "block": f"{COST_UP} past 85",
            "interior_defense": f"{COST_UP} past 85",
        }
        phys_costs = []
        # Height/weight/wingspan effects
        if attr in ("ball_control", "three_point"):
            if self.height > 80 or self.wingspan - self.height > 2:
                phys_costs.append(f"body {COST_UP}")
            elif self.height < 75 and self.wingspan <= self.height:
                phys_costs.append(f"body {COST_DOWN}")
        if attr in ("block", "interior_defense"):
            if self.height > 80 or self.wingspan - self.height > 2:
                phys_costs.append(f"body {COST_DOWN}")
            elif self.height < 75 and self.wingspan <= self.height:
                phys_costs.append(f"body {COST_UP}")
        base_hint = hard_soft.get(attr, "normal")
        if phys_costs:
            base_hint += f" ({'/'.join(phys_costs)})"
        return base_hint

    def _validate(self, player: Player) -> List[str]:
        errors = []
        if not player.name.strip():
            errors.append("Name is required.")
        if self._compute_budget() > self.budget_cap:
            errors.append("Over budget.")
        # Tendencies should normalise to 1.0 groups; we already normalise, so no extra error
        return errors

    def _summary_text(self, player: Player) -> str:
        name = self.build_namer.generate_name(player, position_map={player.player_id: self.position})
        report = self.scouting.scouting_reports([player], role_map={player.player_id: self.position})
        entry = report.get(player.player_id, {})
        lines = [
            f"Name: {player.name}",
            f"Position: {self.position}",
            f"Build: {name}",
            f"Public OVR: {entry.get('public_ovr', '?')}",
            f"Roles: {', '.join(entry.get('role_descriptors', []))}",
            f"Hometown: {self.hometown}",
            f"Height/Weight/Wingspan: {self.height}/{self.weight}/{self.wingspan}",
            f"Points spent: {self._compute_budget()}/{self.budget_cap}",
        ]
        return "\n".join(lines)

    def _details_text(self, player: Player) -> str:
        attrs = player.attributes.__dict__
        tend = player.tendencies.__dict__

        def fmt_full_dict(d: Dict[str, object]) -> str:
            return "\n".join(f"{k}: {v}" for k, v in d.items())

        return f"Attributes:\n{fmt_full_dict(attrs)}\n\nTendencies:\n{fmt_full_dict(tend)}"

    def _save_json(self, player: Player) -> None:
        from pathlib import Path
        out = Path(self.export_path or "player_build.json")
        out.write_text(json.dumps(player.__dict__, default=lambda o: o.__dict__, indent=2), encoding="utf-8")
        self.console.log(f"Saved to {out}")

    def _filter_cities(self, query: str) -> None:
        if not query:
            opts = self.city_options
        else:
            q = query.lower()
            opts = []
            for city in self.city_service._cities:
                label = f"{city['city']}, {city['state_id']}"
                if q in label.lower():
                    opts.append((label, label))
                if len(opts) >= 50:
                    break
        select = self.query_one("#city-select", Select)
        if opts:
            select.set_options(opts)
            select.value = opts[0][1]
            self.hometown = opts[0][1]

    def _selected_city_meta(self) -> Dict[str, str]:
        # best effort lookup for selected hometown
        label = self.hometown
        for city in self.city_service._cities:
            if f"{city['city']}, {city['state_id']}" == label:
                return city
        return {}


if __name__ == "__main__":
    CharacterCreatorApp().run()
