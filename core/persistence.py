from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from core.models import NormalizationReport, ReviewState, WordEntry


def ensure_data_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_normalized(path: Path, entries: list[WordEntry], report: NormalizationReport) -> None:
    ensure_data_dir(path.parent)
    payload = {
        "entries": [entry.to_dict() for entry in entries],
        "report": report.to_dict(),
        "generated_at": date.today().isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_normalized(path: Path) -> tuple[list[WordEntry], dict[str, Any]]:
    if not path.exists():
        return [], {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = [WordEntry.from_dict(item) for item in payload.get("entries", [])]
    report = payload.get("report", {})
    return entries, report


def save_progress(path: Path, states: dict[str, ReviewState], stats: dict[str, Any]) -> None:
    ensure_data_dir(path.parent)
    payload = {
        "states": {word: state.to_dict() for word, state in states.items()},
        "stats": stats,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_progress(path: Path) -> tuple[dict[str, ReviewState], dict[str, Any]]:
    if not path.exists():
        return {}, {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    states = {
        word: ReviewState.from_dict(state)
        for word, state in payload.get("states", {}).items()
    }
    stats = payload.get("stats", {})
    return states, stats


def load_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, Any]) -> None:
    ensure_data_dir(path.parent)
    path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
