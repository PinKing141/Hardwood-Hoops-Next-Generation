from dataclasses import dataclass
from typing import Dict, List

COST_UP = "UP"
COST_DOWN = "DOWN"


@dataclass
class ModifierPreview:
    modifiers: Dict[str, int]
    caps: Dict[str, int]
    cost_arrows: Dict[str, str]
    proto_label: str


def compute_modifiers(position: str, height: int, weight: int, wingspan: int) -> ModifierPreview:
    """
    Lightweight heuristic that follows the design rules:
    - Height: blocks/rebounding/interior up, speed/agility down
    - Weight: strength/interior up, speed/agility down
    - Wingspan: defence/rebounding up, slight shooting/handle down
    All values are small integers for preview only.
    """
    pos_group = _pos_group(position)

    mods: Dict[str, int] = {}
    caps: Dict[str, int] = {}
    costs: Dict[str, str] = {}

    # Height breakpoints (every ~2 inches)
    height_delta = height - _pos_baseline_height(pos_group)
    mods.update(_height_mods(height_delta))
    caps.update(_height_caps(height_delta))
    costs.update(_height_costs(height_delta))

    weight_delta = weight - _pos_baseline_weight(pos_group)
    mods = _combine(mods, _weight_mods(weight_delta))
    caps = _combine(caps, _weight_caps(weight_delta))
    costs.update(_weight_costs(weight_delta))

    wingspan_delta = wingspan - height
    mods = _combine(mods, _wingspan_mods(wingspan_delta))
    caps = _combine(caps, _wingspan_caps(wingspan_delta))
    costs.update(_wingspan_costs(wingspan_delta))

    proto_label = _proto_label(mods)
    mods = _apply_immunity(mods)
    caps = _apply_immunity(caps)

    return ModifierPreview(modifiers=mods, caps=caps, cost_arrows=costs, proto_label=proto_label)


def cost_arrows_by_attribute(position: str, height: int, weight: int, wingspan: int) -> Dict[str, str]:
    """Returns per-attribute cost arrows derived from physical traits."""
    arrows: Dict[str, str] = {}
    preview = compute_modifiers(position, height, weight, wingspan)
    # Map coarse cost signals to specific attributes
    if preview.cost_arrows.get("ball_control") == COST_UP:
        for attr in ("ball_control", "three_point"):
            arrows[attr] = COST_UP
    if preview.cost_arrows.get("ball_control") == COST_DOWN:
        for attr in ("ball_control", "three_point"):
            arrows[attr] = COST_DOWN
    if preview.cost_arrows.get("block") == COST_DOWN or preview.cost_arrows.get("interior_defense") == COST_DOWN:
        for attr in ("block", "interior_defense"):
            arrows[attr] = COST_DOWN
    if preview.cost_arrows.get("block") == COST_UP or preview.cost_arrows.get("interior_defense") == COST_UP:
        for attr in ("block", "interior_defense"):
            arrows[attr] = COST_UP
    if preview.cost_arrows.get("defense") == COST_DOWN:
        for attr in ("perimeter_defense", "steal"):
            arrows[attr] = COST_DOWN
    if preview.cost_arrows.get("defense") == COST_UP:
        for attr in ("perimeter_defense", "steal"):
            arrows[attr] = COST_UP
    if preview.cost_arrows.get("rebounding") == COST_DOWN:
        for attr in ("offensive_rebound", "defensive_rebound"):
            arrows[attr] = COST_DOWN
    if preview.cost_arrows.get("rebounding") == COST_UP:
        for attr in ("offensive_rebound", "defensive_rebound"):
            arrows[attr] = COST_UP
    if preview.cost_arrows.get("speed") == COST_UP:
        for attr in ("speed", "agility"):
            arrows[attr] = COST_UP
    if preview.cost_arrows.get("speed") == COST_DOWN:
        for attr in ("speed", "agility"):
            arrows[attr] = COST_DOWN
    if preview.cost_arrows.get("strength") == COST_DOWN:
        arrows["strength"] = COST_DOWN
    if preview.cost_arrows.get("strength") == COST_UP:
        arrows["strength"] = COST_UP
    return arrows


# --- helper logic ---

def _pos_group(position: str) -> str:
    code = (position or "").upper()
    if code in ("PG", "SG"):
        return "guard"
    if code in ("SF",):
        return "wing"
    if code in ("PF",):
        return "forward"
    if code in ("C",):
        return "center"
    return "wing"


def _pos_baseline_height(group: str) -> int:
    return {"guard": 74, "wing": 78, "forward": 80, "center": 83}.get(group, 78)


def _pos_baseline_weight(group: str) -> int:
    return {"guard": 190, "wing": 205, "forward": 220, "center": 240}.get(group, 205)


def _height_mods(delta: int) -> Dict[str, int]:
    step = delta // 2
    mods = {}
    mods["block"] = 2 * step
    mods["interior_defense"] = 1 * step
    mods["defensive_rebound"] = 1 * step
    mods["offensive_rebound"] = max(0, step)
    mods["speed"] = -1 * step
    mods["agility"] = -1 * step
    return {k: v for k, v in mods.items() if v != 0}


def _height_caps(delta: int) -> Dict[str, int]:
    step = delta // 2
    caps = {}
    caps["block"] = 2 * step
    caps["interior_defense"] = 1 * step
    caps["ball_control"] = -1 * step if delta > 0 else 0
    caps["three_point"] = -1 * step if delta > 0 else 0
    return {k: v for k, v in caps.items() if v != 0}


def _height_costs(delta: int) -> Dict[str, str]:
    if delta == 0:
        return {}
    if delta > 0:
        return {"ball_control": COST_UP, "three_point": COST_UP, "block": COST_DOWN, "interior_defense": COST_DOWN}
    return {"ball_control": COST_DOWN, "three_point": COST_DOWN, "block": COST_UP, "interior_defense": COST_UP}


def _weight_mods(delta: int) -> Dict[str, int]:
    bands = delta // 10
    mods = {}
    mods["strength"] = 2 * bands
    mods["interior_defense"] = 1 * bands
    mods["speed"] = -1 * bands
    mods["agility"] = -1 * bands
    return {k: v for k, v in mods.items() if v != 0}


def _weight_caps(delta: int) -> Dict[str, int]:
    bands = delta // 10
    caps = {}
    caps["strength"] = 1 * bands
    caps["speed"] = -1 * bands if delta > 0 else 0
    caps["agility"] = -1 * bands if delta > 0 else 0
    return {k: v for k, v in caps.items() if v != 0}


def _weight_costs(delta: int) -> Dict[str, str]:
    if delta == 0:
        return {}
    if delta > 0:
        return {"speed": COST_UP, "agility": COST_UP, "strength": COST_DOWN, "interior_defense": COST_DOWN}
    return {"speed": COST_DOWN, "agility": COST_DOWN, "strength": COST_UP, "interior_defense": COST_UP}


def _wingspan_mods(delta: int) -> Dict[str, int]:
    bands = delta // 2
    mods = {}
    mods["block"] = 2 * bands
    mods["steal"] = 1 * bands
    mods["perimeter_defense"] = 1 * bands
    mods["defensive_rebound"] = 1 * bands
    mods["offensive_rebound"] = max(0, bands)
    return {k: v for k, v in mods.items() if v != 0}


def _wingspan_caps(delta: int) -> Dict[str, int]:
    bands = delta // 2
    caps = {}
    caps["block"] = 1 * bands
    caps["perimeter_defense"] = 1 * bands
    caps["three_point"] = -1 * bands if delta > 0 else 0
    caps["ball_control"] = -1 * bands if delta > 0 else 0
    return {k: v for k, v in caps.items() if v != 0}


def _wingspan_costs(delta: int) -> Dict[str, str]:
    if delta == 0:
        return {}
    if delta > 0:
        return {"ball_control": COST_UP, "three_point": COST_UP, "defense": COST_DOWN, "rebounding": COST_DOWN}
    return {"ball_control": COST_DOWN, "three_point": COST_DOWN, "defense": COST_UP, "rebounding": COST_UP}


def _combine(base: Dict[str, int], extra: Dict[str, int]) -> Dict[str, int]:
    out = dict(base)
    for k, v in extra.items():
        out[k] = out.get(k, 0) + v
    return out


def _apply_immunity(values: Dict[str, int]) -> Dict[str, int]:
    immune = {"free_throw", "passing", "offensive_iq", "defensive_iq", "hustle", "clutch", "consistency", "decision_discipline"}
    return {k: v for k, v in values.items() if k not in immune}


def _proto_label(mods: Dict[str, int]) -> str:
    if mods.get("block", 0) >= 4:
        return "Long-Arm Defender"
    if mods.get("strength", 0) >= 4:
        return "Big Body"
    if mods.get("speed", 0) <= -3:
        return "Interior Lean"
    return "Balanced"
