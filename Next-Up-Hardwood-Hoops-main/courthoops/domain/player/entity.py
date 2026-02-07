from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PlayerAttributes:
    # Offensive
    layup: int
    dunk: int
    inside: int
    mid_range: int
    three_point: int
    free_throw: int
    offensive_rebound: int
    # Playmaking
    ball_control: int
    passing: int
    # Defense
    defensive_rebound: int
    perimeter_defense: int
    interior_defense: int
    steal: int
    block: int
    # Athleticism
    speed: int
    agility: int
    vertical: int
    strength: int
    stamina: int
    # Mentals
    offensive_iq: int
    defensive_iq: int
    hustle: int
    # Hidden
    potential: int
    injury_proneness: int
    clutch: int
    consistency: int
    decision_discipline: int


@dataclass
class PlayerTendencies:
    # Legacy scalar tendencies (kept for backward compatibility)
    shot_selection: float = 0.5
    aggression: float = 0.5

    # Normalized behaviour vectors (should sum to 1.0 within each group)
    shot_profile: List[float] = field(default_factory=lambda: [0.4, 0.25, 0.35])  # close, mid, three
    rim_aggression: List[float] = field(default_factory=lambda: [0.6, 0.4])  # layup, dunk
    shot_creation: List[float] = field(default_factory=lambda: [0.4, 0.25, 0.35])  # catch, pull-up, drive-generated
    playmaking_bias: List[float] = field(default_factory=lambda: [0.4, 0.35, 0.25])  # score-first, pass-first, reactive
    pass_profile: List[float] = field(default_factory=lambda: [0.4, 0.25, 0.35])  # kick-out, interior dump, swing/reset

    defensive_style: List[float] = field(default_factory=lambda: [0.45, 0.35, 0.20])  # containment, disruption, gambler
    help_defense: List[float] = field(default_factory=lambda: [0.35, 0.35, 0.30])  # early, late, stay home
    rebound_bias: List[float] = field(default_factory=lambda: [0.4, 0.2, 0.4])  # crash, leak out, balanced
    athletic_usage: List[float] = field(default_factory=lambda: [0.3, 0.25, 0.25, 0.2])  # straight-line, change-of-pace, vertical, physical


@dataclass
class PlayerPersonality:
    work_ethic: float = 0.5
    coachability: float = 0.5
    competitiveness: float = 0.5


@dataclass
class Player:
    player_id: str
    name: str
    class_year: str  # HS FR/SO/JR/SR, College FR/SO/JR/SR, etc.
    attributes: PlayerAttributes
    tendencies: PlayerTendencies
    personality: PlayerPersonality
    fatigue: float = 0.0
    injured: bool = False
    injury_days: int = 0  # remaining days out
    injury_type: Optional[str] = None
    injury_severity: Optional[str] = None
    injury_status: Optional[str] = None
    stats: Dict[str, float] = field(default_factory=dict)
    minutes_allocation: float = 20.0  # target minutes per game for lineup planning
    badges: List[str] = field(default_factory=list)
    archetype: Optional[str] = None

    def reset_fatigue(self) -> None:
        self.fatigue = 0.0
