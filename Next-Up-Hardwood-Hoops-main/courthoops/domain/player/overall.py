from __future__ import annotations

from typing import Dict, Tuple

from courthoops.domain.player.entity import Player


def _weighted_average(weights: Dict[str, float], values: Dict[str, float]) -> float:
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 50.0
    score = sum(weights[key] * values.get(key, 50.0) for key in weights)
    return score / total_weight


def _clamp_rating(value: float, minimum: float = 25.0, maximum: float = 99.0) -> float:
    return max(minimum, min(maximum, value))


def _role_bias(role: str) -> Dict[str, float]:
    # Light role nudges; they are applied multiplicatively to offense sub-weights.
    if role == "guard":
        return {"three_point": 1.05, "ball_control": 1.05, "passing": 1.05, "inside": 0.95, "block": 0.95}
    if role == "wing":
        return {"mid_range": 1.05, "perimeter_defense": 1.05, "three_point": 1.02}
    if role == "big":
        return {"inside": 1.05, "offensive_rebound": 1.05, "defensive_rebound": 1.05, "interior_defense": 1.05, "block": 1.05, "three_point": 0.95}
    return {}


def compute_true_overall(player: Player, role: str = "wing") -> float:
    """
    Hidden overall used for AI evaluation (not for gameplay rolls).
    Weighted by category with light role bias to avoid archetype inflation.
    """
    attrs = player.attributes
    role_multiplier = _role_bias(role)

    offense_weights = {
        "layup": 8,
        "dunk": 7,
        "inside": 7 * role_multiplier.get("inside", 1.0),
        "mid_range": 5 * role_multiplier.get("mid_range", 1.0),
        "three_point": 5 * role_multiplier.get("three_point", 1.0),
        "free_throw": 3,
        "offensive_rebound": 5 * role_multiplier.get("offensive_rebound", 1.0),
        "ball_control": 5 * role_multiplier.get("ball_control", 1.0),
        "passing": 10 * role_multiplier.get("passing", 1.0),
    }

    defense_weights = {
        "perimeter_defense": 8 * role_multiplier.get("perimeter_defense", 1.0),
        "interior_defense": 8 * role_multiplier.get("interior_defense", 1.0),
        "defensive_rebound": 6 * role_multiplier.get("defensive_rebound", 1.0),
        "steal": 4,
        "block": 4 * role_multiplier.get("block", 1.0),
    }

    athletic_weights = {"speed": 6, "agility": 5, "vertical": 4, "strength": 3, "stamina": 2}
    mental_weights = {"offensive_iq": 8, "defensive_iq": 5, "hustle": 2}

    value_map = attrs.__dict__
    offense_score = _weighted_average(offense_weights, value_map)
    defense_score = _weighted_average(defense_weights, value_map)
    athletic_score = _weighted_average(athletic_weights, value_map)
    mental_score = _weighted_average(mental_weights, value_map)

    overall = (
        0.35 * offense_score
        + 0.30 * defense_score
        + 0.20 * athletic_score
        + 0.15 * mental_score
    )
    return _clamp_rating(overall)


def compute_public_overall(player: Player, role: str = "wing") -> Tuple[float, float]:
    """
    Public-facing OVR (perceived) derived from true overall with noise from consistency/potential.
    Returns (true_overall, public_overall).
    """
    true_ovr = compute_true_overall(player, role=role)
    consistency = player.attributes.consistency
    potential = player.attributes.potential
    # Bias: better potential bumps perception slightly; low consistency widens variance.
    bias = (potential - 50) * 0.03
    noise_range = max(3.0, (100 - consistency) * 0.07)
    # Deterministic pseudo-noise from player id for reproducibility in domain
    pseudo = (hash(player.player_id) % 100) / 100.0  # 0..0.99
    noise = (pseudo - 0.5) * 2 * noise_range  # centered around 0
    public = _clamp_rating(true_ovr + bias + noise)
    return true_ovr, public
