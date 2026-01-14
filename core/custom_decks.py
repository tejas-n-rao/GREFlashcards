from __future__ import annotations

import json
from pathlib import Path

from core.models import SourceRef, WordEntry
from core.persistence import ensure_data_dir
from core.sets import CardSet


CUSTOM_SOURCE = "Custom Decks"


def _clean_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _unique_words(words: list[str]) -> list[str]:
    seen = set()
    unique = []
    for word in words:
        key = word.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(word)
    return unique


def load_custom_decks(path: Path) -> dict[str, list[WordEntry]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    decks: dict[str, list[WordEntry]] = {}
    for deck in payload.get("decks", []):
        name = str(deck.get("name", "")).strip()
        if not name:
            continue
        cards = []
        for card in deck.get("cards", []):
            word = str(card.get("word", "")).strip()
            if not word:
                continue
            cards.append(
                WordEntry(
                    word=word,
                    meaning=card.get("meaning"),
                    example=card.get("example"),
                    pos=card.get("pos"),
                    synonyms=list(card.get("synonyms", [])),
                    mnemonics=list(card.get("mnemonics", [])),
                    tags=list(card.get("tags", [])),
                    sources=[SourceRef(filename=CUSTOM_SOURCE, sheet=name)],
                )
            )
        decks[name] = cards
    return decks


def save_custom_decks(path: Path, decks: dict[str, list[WordEntry]]) -> None:
    ensure_data_dir(path.parent)
    payload = {
        "decks": [
            {
                "name": name,
                "cards": [
                    {
                        "word": card.word,
                        "meaning": card.meaning,
                        "example": card.example,
                        "pos": card.pos,
                        "synonyms": card.synonyms,
                        "mnemonics": card.mnemonics,
                        "tags": card.tags,
                    }
                    for card in cards
                ],
            }
            for name, cards in decks.items()
        ]
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_custom_sets(decks: dict[str, list[WordEntry]]) -> dict[str, CardSet]:
    sets: dict[str, CardSet] = {}
    for name, cards in decks.items():
        words = _unique_words([card.word for card in cards])
        set_name = f"{CUSTOM_SOURCE} :: {name}"
        sets[set_name] = CardSet(name=set_name, word_keys=words)
    return sets


def parse_list_field(raw: str) -> list[str]:
    return _clean_list(raw)
