from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from core.deck_progress import DeckSessionSettings
from core.models import DeckReviewState, NormalizationReport, ReviewState, WordEntry


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


def save_deck_progress(
    path: Path,
    decks: dict[str, dict[str, DeckReviewState]],
    settings: dict[str, DeckSessionSettings],
) -> None:
    ensure_data_dir(path.parent)
    payload = {
        "decks": {
            deck_id: {
                "settings": settings.get(deck_id, DeckSessionSettings()).to_dict(),
                "words": {word_id: state.to_dict() for word_id, state in words.items()},
            }
            for deck_id, words in decks.items()
        }
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_deck_progress(
    path: Path,
) -> tuple[dict[str, dict[str, DeckReviewState]], dict[str, DeckSessionSettings]]:
    if not path.exists():
        return {}, {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    deck_states: dict[str, dict[str, DeckReviewState]] = {}
    deck_settings: dict[str, DeckSessionSettings] = {}
    for deck_id, deck_payload in payload.get("decks", {}).items():
        words = {
            word_id: DeckReviewState.from_dict(state)
            for word_id, state in deck_payload.get("words", {}).items()
        }
        deck_states[deck_id] = words
        settings_payload = deck_payload.get("settings", {})
        deck_settings[deck_id] = DeckSessionSettings.from_dict(settings_payload)
    return deck_states, deck_settings


def load_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(path: Path, cache: dict[str, Any]) -> None:
    ensure_data_dir(path.parent)
    path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
