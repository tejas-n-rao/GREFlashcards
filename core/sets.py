from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from core.models import WordEntry


@dataclass(frozen=True)
class CardSet:
    name: str
    word_keys: list[str]


def build_sets(entries: list[WordEntry]) -> dict[str, CardSet]:
    pooled = [entry.word for entry in entries]
    sets: dict[str, list[str]] = {"Pooled": pooled}

    by_file = defaultdict(list)
    by_sheet = defaultdict(list)
    by_subcategory = defaultdict(list)

    for entry in entries:
        for source in entry.sources:
            by_file[f"{source.filename}"].append(entry.word)
            by_sheet[f"{source.filename} :: {source.sheet}"].append(entry.word)
            if source.subcategory:
                by_subcategory[
                    f"{source.filename} :: {source.sheet} :: {source.subcategory}"
                ].append(entry.word)

    for name, words in {**by_file, **by_sheet, **by_subcategory}.items():
        sets[name] = words

    normalized_sets: dict[str, CardSet] = {}
    for name, words in sets.items():
        seen = set()
        unique = []
        for word in words:
            key = word.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(word)
        normalized_sets[name] = CardSet(name=name, word_keys=unique)

    return normalized_sets
