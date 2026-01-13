from __future__ import annotations

from core.models import WordEntry


def entry_map(entries: list[WordEntry]) -> dict[str, WordEntry]:
    return {entry.word.lower(): entry for entry in entries}


def get_entry(entries: list[WordEntry], word: str) -> WordEntry | None:
    return entry_map(entries).get(word.lower())
