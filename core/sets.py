from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass

from config import SET_CHUNK_SIZE, SET_SHUFFLE_SEED
from core.models import WordEntry


@dataclass(frozen=True)
class CardSet:
    name: str
    word_keys: list[str]


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


def _shuffled(words: list[str], seed: int) -> list[str]:
    rng = random.Random(seed)
    shuffled = list(words)
    rng.shuffle(shuffled)
    return shuffled


def _chunk(words: list[str], size: int) -> list[list[str]]:
    return [words[i : i + size] for i in range(0, len(words), size)]


def build_sets(entries: list[WordEntry]) -> dict[str, CardSet]:
    pooled = _unique_words([entry.word for entry in entries])
    pooled = _shuffled(pooled, SET_SHUFFLE_SEED)
    sets: dict[str, list[str]] = {"Pooled": pooled}

    by_file = defaultdict(list)
    by_subcategory = defaultdict(list)
    for entry in entries:
        for source in entry.sources:
            by_file[source.filename].append(entry.word)
            if source.subcategory:
                by_subcategory[f"{source.filename} :: {source.subcategory}"].append(entry.word)

    for filename, words in by_file.items():
        unique = _unique_words(words)
        shuffled = _shuffled(unique, SET_SHUFFLE_SEED + hash(filename) % 10_000)
        sets[filename] = shuffled
        for idx, chunk in enumerate(_chunk(shuffled, SET_CHUNK_SIZE), start=1):
            sets[f"{filename} :: Set {idx}"] = chunk

    for name, words in by_subcategory.items():
        unique = _unique_words(words)
        shuffled = _shuffled(unique, SET_SHUFFLE_SEED + hash(name) % 10_000)
        sets[name] = shuffled

    for idx, chunk in enumerate(_chunk(pooled, SET_CHUNK_SIZE), start=1):
        sets[f"Pooled :: Set {idx}"] = chunk

    return {name: CardSet(name=name, word_keys=words) for name, words in sets.items()}
