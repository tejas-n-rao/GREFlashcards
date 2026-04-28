from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CUSTOM_DECKS_PATH, EXCEL_FILES
from core.custom_decks import load_custom_decks, save_custom_decks
from core.models import SourceRef, WordEntry
from core.normalization import normalize_excel_files
import core.normalization as normalization_module


DECK_NAME = "Consolidated Newest"
CUSTOM_SOURCE = "Custom Decks"

_NON_WORD_CHARS = re.compile(r"[^a-zA-Z0-9' -]+")
_MULTI_SPACE = re.compile(r"\s+")


def _safe_wordnet():
    try:
        from nltk.corpus import wordnet as wn
    except Exception:
        return None
    return wn


def _clean_text(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    text = _NON_WORD_CHARS.sub(" ", text)
    text = _MULTI_SPACE.sub(" ", text).strip()
    return text or None


def _clean_list(values: list[str]) -> list[str]:
    cleaned = []
    seen = set()
    for raw in values:
        text = _clean_text(raw.replace("_", " "))
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
    return cleaned


def _wordnet_payload(word: str) -> dict[str, str | list[str] | None]:
    wn = _safe_wordnet()
    if wn is None:
        return {"meaning": None, "example": None, "pos": None, "synonyms": [], "antonyms": []}

    try:
        synsets = wn.synsets(word)
    except Exception:
        synsets = []
    if not synsets:
        return {"meaning": None, "example": None, "pos": None, "synonyms": [], "antonyms": []}

    first = synsets[0]
    pos_map = {"n": "Noun", "v": "Verb", "a": "Adjective", "s": "Adjective", "r": "Adverb"}
    meaning = _clean_text(first.definition())
    examples = first.examples() or []
    example = _clean_text(examples[0]) if examples else None
    pos = pos_map.get(first.pos())

    synonyms: list[str] = []
    antonyms: list[str] = []
    for synset in synsets:
        for lemma in synset.lemmas():
            lemma_name = lemma.name().replace("_", " ")
            if lemma_name.lower() != word.lower():
                synonyms.append(lemma_name)
            for antonym in lemma.antonyms():
                antonym_name = antonym.name().replace("_", " ")
                if antonym_name.lower() != word.lower():
                    antonyms.append(antonym_name)

    return {
        "meaning": meaning,
        "example": example,
        "pos": pos,
        "synonyms": _clean_list(synonyms),
        "antonyms": _clean_list(antonyms),
    }


def _combine_limited(word: str, primary: list[str], secondary: list[str], limit: int = 3) -> list[str]:
    seen = {word.lower()}
    result: list[str] = []
    for candidate in primary + secondary:
        cleaned = _clean_text(candidate)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def _is_placeholder_example(word: str, example: str | None) -> bool:
    if not example:
        return True
    cleaned = example.strip().strip(".").lower()
    return cleaned == word.strip().lower()


def build_consolidated_entries() -> list[WordEntry]:
    original_include = dict(normalization_module.INCLUDE_SHEETS)
    original_exclude = dict(normalization_module.EXCLUDE_SHEETS)
    normalization_module.INCLUDE_SHEETS.clear()
    normalization_module.EXCLUDE_SHEETS.clear()
    try:
        entries, _ = normalize_excel_files(EXCEL_FILES)
    finally:
        normalization_module.INCLUDE_SHEETS.clear()
        normalization_module.INCLUDE_SHEETS.update(original_include)
        normalization_module.EXCLUDE_SHEETS.clear()
        normalization_module.EXCLUDE_SHEETS.update(original_exclude)

    entries = sorted(entries, key=lambda item: item.word.lower())
    consolidated: list[WordEntry] = []
    for entry in entries:
        wn = _wordnet_payload(entry.word)
        meaning = _clean_text(entry.meaning) or wn["meaning"]  # type: ignore[index]
        example = None if _is_placeholder_example(entry.word, entry.example) else _clean_text(entry.example)
        example = example or wn["example"]  # type: ignore[index]
        pos = _clean_text(entry.pos) or wn["pos"]  # type: ignore[index]

        synonyms = _combine_limited(
            entry.word,
            _clean_list(entry.synonyms),
            list(wn["synonyms"]),  # type: ignore[arg-type,index]
            limit=3,
        )
        antonyms = _combine_limited(
            entry.word,
            [],
            list(wn["antonyms"]),  # type: ignore[arg-type,index]
            limit=3,
        )

        consolidated.append(
            WordEntry(
                word=entry.word.strip(),
                meaning=meaning,
                example=example,
                pos=pos,
                synonyms=synonyms,
                antonyms=antonyms,
                mnemonics=_clean_list(entry.mnemonics)[:2],
                tags=["consolidated", "newest"],
                sources=[SourceRef(filename=CUSTOM_SOURCE, sheet=DECK_NAME)],
            )
        )
    return consolidated


def main() -> None:
    decks = load_custom_decks(CUSTOM_DECKS_PATH)
    decks[DECK_NAME] = build_consolidated_entries()
    save_custom_decks(CUSTOM_DECKS_PATH, decks)

    card_count = len(decks[DECK_NAME])
    with_meaning = sum(1 for card in decks[DECK_NAME] if card.meaning)
    with_example = sum(1 for card in decks[DECK_NAME] if card.example)
    with_synonyms = sum(1 for card in decks[DECK_NAME] if card.synonyms)
    with_antonyms = sum(1 for card in decks[DECK_NAME] if card.antonyms)

    print(f"Deck: {DECK_NAME}")
    print(f"Cards: {card_count}")
    print(f"Meaning filled: {with_meaning}")
    print(f"Example filled: {with_example}")
    print(f"Synonyms filled: {with_synonyms}")
    print(f"Antonyms filled: {with_antonyms}")


if __name__ == "__main__":
    main()
