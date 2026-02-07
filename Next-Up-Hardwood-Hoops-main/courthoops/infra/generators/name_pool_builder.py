"""
One-off utility to curate US-flavored name pools from large pickle dictionaries.

Each input pickle is expected to be a dict:
    name -> {"country": {"US": float, ...}, "gender": {"M": float, "F": float}}

Outputs two JSON files with lightweight lists for in-game use.
This avoids loading 150MB+ pickles during runtime.
"""
from __future__ import annotations

import argparse
import json
import pickle
import re
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

NameMeta = Dict[str, Dict[str, float]]


VALID_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$")


def strip_diacritics(text: str) -> str:
    """ASCII-safe fallback for display names."""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def clean_name(name: str) -> str:
    """Trim and collapse spaces."""
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    return name


def looks_junky(name: str) -> bool:
    """Reject names that look like initials or contain disallowed characters."""
    if len(name) < 2 or len(name) > 24:
        return True
    if not VALID_RE.match(name):
        return True
    parts = name.split(" ")
    if len(parts) >= 2 and all(len(p) == 1 for p in parts):
        return True
    if any(char.isdigit() for char in name):
        return True
    return False


def load_pickle(path: Path) -> Dict[str, NameMeta]:
    with path.open("rb") as f:
        return pickle.load(f)


def filter_first_names(
    data: Dict[str, NameMeta],
    us_threshold: float = 0.10,
    gender_threshold: float = 0.80,
    gender_key: str = "M",
    ascii_display: bool = False,
) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for raw, meta in data.items():
        name = clean_name(raw)
        if looks_junky(name):
            continue
        us_prob = meta.get("country", {}).get("US", 0.0)
        gender_prob = meta.get("gender", {}).get(gender_key, 0.0)
        if us_prob < us_threshold or gender_prob < gender_threshold:
            continue
        weight = us_prob * gender_prob
        record: Dict[str, object] = {"name": strip_diacritics(name) if ascii_display else name, "weight": weight}
        if ascii_display:
            record["original_name"] = name
        out.append(record)
    return out


def filter_last_names(
    data: Dict[str, NameMeta],
    us_threshold: float = 0.05,
    ascii_display: bool = False,
) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for raw, meta in data.items():
        name = clean_name(raw)
        if looks_junky(name):
            continue
        us_prob = meta.get("country", {}).get("US", 0.0)
        if us_prob < us_threshold:
            continue
        record: Dict[str, object] = {"name": strip_diacritics(name) if ascii_display else name, "weight": us_prob}
        if ascii_display:
            record["original_name"] = name
        out.append(record)
    return out


def build_pools(
    first_pickle: Path,
    last_pickle: Path,
    out_first_json: Path,
    out_last_json: Path,
    ascii_display: bool = False,
    us_first_threshold: float = 0.10,
    male_threshold: float = 0.80,
    us_last_threshold: float = 0.05,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    first_data = load_pickle(first_pickle)
    last_data = load_pickle(last_pickle)

    first_pool = filter_first_names(
        first_data,
        us_threshold=us_first_threshold,
        gender_threshold=male_threshold,
        gender_key="M",
        ascii_display=ascii_display,
    )
    last_pool = filter_last_names(last_data, us_threshold=us_last_threshold, ascii_display=ascii_display)

    out_first_json.parent.mkdir(parents=True, exist_ok=True)
    out_last_json.parent.mkdir(parents=True, exist_ok=True)

    out_first_json.write_text(json.dumps(first_pool, ensure_ascii=False, indent=2), encoding="utf-8")
    out_last_json.write_text(json.dumps(last_pool, ensure_ascii=False, indent=2), encoding="utf-8")
    return first_pool, last_pool


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Curate US-flavored name pools from pickle datasets.")
    parser.add_argument("--first-pickle", type=Path, required=True, help="Path to first_names.pkl")
    parser.add_argument("--last-pickle", type=Path, required=True, help="Path to last_names.pkl")
    parser.add_argument("--out-first", type=Path, default=Path("us_male_first_names.json"))
    parser.add_argument("--out-last", type=Path, default=Path("us_last_names.json"))
    parser.add_argument("--ascii-display", action="store_true", help="Store ASCII display names (keeps originals).")
    parser.add_argument("--us-first-threshold", type=float, default=0.10)
    parser.add_argument("--male-threshold", type=float, default=0.80)
    parser.add_argument("--us-last-threshold", type=float, default=0.05)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    build_pools(
        first_pickle=args.first_pickle,
        last_pickle=args.last_pickle,
        out_first_json=args.out_first,
        out_last_json=args.out_last,
        ascii_display=args.ascii_display,
        us_first_threshold=args.us_first_threshold,
        male_threshold=args.male_threshold,
        us_last_threshold=args.us_last_threshold,
    )


if __name__ == "__main__":
    main()
