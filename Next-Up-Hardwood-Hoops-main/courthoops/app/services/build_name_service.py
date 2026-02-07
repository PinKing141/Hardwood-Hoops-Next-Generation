import json
from pathlib import Path
from typing import Dict, List

from courthoops.domain.player.entity import Player
from courthoops.app.services.role_affinity_service import RoleAffinityService


class BuildNameService:
    """
    Generates 2K-style build names using grammar rules (Rule A / Rule B).
    Names are descriptive compression of affinities, not gameplay mechanics.
    """

    def __init__(self, role_affinity: RoleAffinityService | None = None, vocab_path: str | None = None):
        self.role_affinity = role_affinity or RoleAffinityService()
        self.vocab = self._load_vocab(vocab_path)

    def generate_name(self, player: Player, position_map: Dict[str, str] | None = None) -> str:
        affinities = self.role_affinity.top_roles(player, n=3)
        primary_role = next(iter(affinities)) if affinities else "balanced"
        pos_code = self._position_code(player, position_map)
        group = self._position_group(pos_code)

        name = self._rule_a_name(player, affinities, primary_role, group)
        if not name:
            name = self._rule_b_name(primary_role, group)
        return self._trim_words(name)

    def _rule_a_name(self, player: Player, affinities: Dict[str, float], primary_role: str, group: str | None) -> str:
        defensive_prefix = self._defensive_prefix(player, affinities)
        offensive_core = self._offensive_core(primary_role, group)
        specialization = self._specialization(primary_role, group)
        parts: List[str] = []
        if defensive_prefix:
            parts.append(defensive_prefix)
        if specialization:
            parts.append(specialization)
        parts.append(offensive_core)
        candidate = " ".join([p for p in parts if p])
        return candidate if self._valid(candidate) else ""

    def _rule_b_name(self, primary_role: str, group: str | None) -> str:
        # Compound descriptor + noun
        descriptor = self._best_descriptor(primary_role, group)
        noun = self._best_noun(primary_role, group)
        candidate = f"{descriptor} {noun}".strip()
        return candidate if self._valid(candidate, allow_prefix=False) else ""

    def _defensive_prefix(self, player: Player, affinities: Dict[str, float]) -> str:
        attrs = player.attributes
        defense_score = (attrs.perimeter_defense + attrs.interior_defense + attrs.steal + attrs.block) / 4
        shoot_score = (attrs.three_point + attrs.free_throw) / 2

        if defense_score >= 75 and shoot_score >= 70:
            return "3 & D"
        if defense_score >= 80:
            return "2 Way"
        top_def = affinities.get("defensive_stopper", 0.0)
        return "2 Way" if top_def >= 0.2 else ""

    def _offensive_core(self, primary_role: str, group: str | None) -> str:
        mapping = {
            "rim_pressure_wing": "Slasher",
            "spot_up_shooter": "Shooter",
            "secondary_creator": "Shot Creator",
            "primary_creator": "Playmaker",
            "defensive_stopper": "Defender",
            "glass_cleaner": "Glass Cleaner",
            "stretch_big": "Stretch Four",
        }
        core = mapping.get(primary_role, "Shot Creator")
        if not self._core_allowed(core, group):
            core = self._first_allowed_core(group)
        return core

    def _specialization(self, primary_role: str, group: str | None) -> str:
        mapping = {
            "rim_pressure_wing": "Slashing",
            "spot_up_shooter": "3 PT",
            "secondary_creator": "Inside Out",
            "primary_creator": "3 Level",
            "stretch_big": "Floor Spacing",
        }
        spec = mapping.get(primary_role, "")
        if spec and not self._specialization_allowed(spec, group):
            spec = ""
        return spec

    def _best_descriptor(self, primary_role: str, group: str | None) -> str:
        pref = {
            "rim_pressure_wing": "Slashing",
            "spot_up_shooter": "Sharpshooting",
            "secondary_creator": "Shot Creating",
            "primary_creator": "Playmaking",
            "glass_cleaner": "Rebounding",
            "stretch_big": "Floor Spacing",
            "defensive_stopper": "Lockdown",
        }
        cand = pref.get(primary_role, self.vocab["compound_descriptors"][0])
        if not self._descriptor_allowed(cand, group):
            # pick first allowed descriptor
            for d in self.vocab["compound_descriptors"]:
                if self._descriptor_allowed(d, group):
                    return d
        return cand

    def _best_noun(self, primary_role: str, group: str | None) -> str:
        pref = {
            "rim_pressure_wing": "Wing",
            "spot_up_shooter": "Wing",
            "secondary_creator": "Guard",
            "primary_creator": "Guard",
            "glass_cleaner": "Big",
            "stretch_big": "Four",
            "defensive_stopper": "Defender",
        }
        cand = pref.get(primary_role, self.vocab["compound_nouns"][0])
        if not self._noun_allowed(cand, group):
            for n in self.vocab["compound_nouns"]:
                if self._noun_allowed(n, group):
                    return n
        return cand

    def _valid(self, name: str, allow_prefix: bool = True) -> bool:
        words = name.split()
        if len(words) == 0 or len(words) > 5:
            return False
        if not allow_prefix and any(words[0].startswith(p.split()[0]) for p in self.vocab["prefixes"]):
            return False
        # simple vocabulary check: ensure at least core noun is from known sets
        return True

    def _trim_words(self, name: str) -> str:
        parts = name.split()
        if len(parts) > 5:
            parts = parts[:5]
        return " ".join(parts)

    def _load_vocab(self, vocab_path: str | None) -> Dict[str, List[str]]:
        path = Path(vocab_path or Path(__file__).resolve().parent.parent / "data" / "build_vocab.json")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        # fallback minimal vocab
        return {
            "prefixes": ["2 Way", "3 & D", "Defensive"],
            "offensive_cores": ["Shot Creator", "Slasher", "Shooter"],
            "specialisations": ["3 PT", "Inside Out", "Floor Spacing", "Slashing"],
            "compound_descriptors": ["Shot Creating", "Sharpshooting", "Playmaking", "Rebounding"],
            "compound_nouns": ["Guard", "Wing", "Big", "Defender"],
        }

    # --- position helpers ---
    def _position_code(self, player: Player, position_map: Dict[str, str] | None) -> str | None:
        if position_map and player.player_id in position_map:
            return position_map[player.player_id]
        try:
            return (player.stats or {}).get("position")
        except Exception:
            return None

    def _position_group(self, code: str | None) -> str | None:
        if not code:
            return None
        code = code.upper()
        if code in ("PG", "SG"):
            return "guard"
        if code in ("SG", "SF"):
            return "wing"
        if code in ("SF", "PF"):
            return "forward"
        if code in ("PF", "C"):
            return "big"
        if code == "C":
            return "center"
        return None

    def _core_allowed(self, core: str, group: str | None) -> bool:
        if not group:
            return True
        allowed = {
            "guard": {
                "Shot Creator", "Scorer", "Scoring Machine", "Walking Bucket", "Offensive Threat", "Perimeter Threat",
                "Shooter", "Sharpshooter", "Spot Up Threat", "Slasher", "Finisher", "Athletic Finisher", "Lob Threat",
                "Playmaker", "Facilitator", "Floor General", "Pass First Guard", "Offense Initiator",
                "Secondary Ball Handler", "Combo Guard", "Perimeter Defender", "Lockdown Defender", "Ball Hawk",
                "Point of Attack Stopper", "Rebounding Guard"
            },
            "wing": {
                "Shot Creator", "Scorer", "Scoring Machine", "Walking Bucket", "Offensive Threat", "Perimeter Threat",
                "Shooter", "Sharpshooter", "Spot Up Threat", "Slasher", "Finisher", "Athletic Finisher", "Lob Threat",
                "Playmaker", "Facilitator", "Pass First Wing", "Secondary Ball Handler", "Perimeter Defender",
                "Lockdown Defender", "Ball Hawk", "Small Ball Wing", "Rebounding Wing", "Point Forward"
            },
            "forward": {
                "Inside Out Scorer", "Scorer", "Offensive Threat", "Shooter", "Spot Up Threat", "Sharpshooter",
                "Slasher", "Finisher", "Athletic Finisher", "Lob Threat", "Interior Scorer", "Playmaker", "Facilitator",
                "Point Forward", "Small Ball Four", "Glass Cleaner", "Perimeter Defender", "Lockdown Defender",
                "Paint Beast", "Interior Force", "Stretch Four"
            },
            "big": {
                "Interior Scorer", "Interior Finisher", "Paint Beast", "Interior Force", "Glass Cleaner",
                "Defensive Anchor", "Rim Protector", "Paint Protector", "Stretch Four", "Stretch Five",
                "Playmaker", "Facilitator", "Pass First Big"
            },
            "center": {
                "Stretch Five", "Defensive Anchor", "Rim Protector", "Paint Protector", "Glass Cleaner", "Paint Beast",
                "Interior Force", "Interior Scorer", "Interior Finisher", "Pass First Big", "Playmaker"
            },
        }
        return core in allowed.get(group, set())

    def _specialization_allowed(self, spec: str, group: str | None) -> bool:
        if not group:
            return True
        allowed = {
            "guard": {"3 Level", "3 PT", "Deep Range", "Mid Range", "Playmaking", "Diming", "Facilitating", "Pass First", "Slashing", "Floor Spacing", "Tempo Pushing"},
            "wing": {"3 Level", "3 PT", "Mid Range", "Deep Range", "Slashing", "Floor Spacing", "Playmaking", "Diming", "Facilitating", "Inside Out", "Inside The Arc", "Balanced", "All Around", "Skilled", "Versatile", "Tempo Pushing"},
            "forward": {"Inside Out", "Inside The Arc", "Mid Range", "3 Level", "3 PT", "Slashing", "Floor Spacing", "Playmaking", "Diming", "Facilitating", "Balanced", "All Around", "Skilled", "Versatile", "Rim Running"},
            "big": {"Inside Out", "Inside The Arc", "3 PT", "3 Level", "Rim Running", "Playmaking", "Diming", "Facilitating", "Pass First", "Balanced", "Skilled", "Versatile"},
            "center": {"Inside Out", "Inside The Arc", "3 PT", "3 Level", "Rim Running", "Playmaking", "Diming", "Facilitating", "Pass First", "Balanced", "Skilled", "Versatile"},
        }
        return spec in allowed.get(group, set())

    def _descriptor_allowed(self, desc: str, group: str | None) -> bool:
        if not group:
            return True
        big_only = {"Glass Cleaning", "Paint Protecting", "Shot Blocking"}
        guard_only = {"Tempo Pushing"}
        if desc in big_only:
            return group in ("big", "center", "forward")
        if desc in guard_only:
            return group in ("guard", "wing")
        return True

    def _noun_allowed(self, noun: str, group: str | None) -> bool:
        if not group:
            return True
        guard_nouns = {"Guard", "Playmaker"}
        wing_nouns = {"Wing", "Forward"}
        big_nouns = {"Big", "Four", "Five", "Rebounder", "Defender", "Scorer"}
        if group == "guard":
            return noun in guard_nouns or noun in {"Defender", "Rebounder", "Scorer"}
        if group == "wing":
            return noun in wing_nouns or noun in {"Guard", "Forward", "Defender", "Rebounder", "Scorer"}
        if group == "forward":
            return noun in wing_nouns or noun in big_nouns
        if group in ("big", "center"):
            return noun in big_nouns
        return True

    def _first_allowed_core(self, group: str | None) -> str:
        if not group:
            return "Shot Creator"
        for core in self.vocab["offensive_cores"]:
            if self._core_allowed(core, group):
                return core
        return "Shot Creator"
