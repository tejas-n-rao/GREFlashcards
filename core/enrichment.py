from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from core.models import WordEntry


@dataclass
class EnrichmentConfig:
    enable_openai: bool
    openai_model: str
    max_calls_per_run: int
    enrich_only_when_missing: bool


def _safe_import_wordnet():
    try:
        from nltk.corpus import wordnet as wn
    except Exception:
        return None
    return wn


def _wordnet_lookup(word: str) -> dict[str, Any]:
    wn = _safe_import_wordnet()
    if wn is None:
        return {}

    try:
        synsets = wn.synsets(word)
    except Exception:
        return {}
    if not synsets:
        return {}

    pos_map = {"n": "Noun", "v": "Verb", "a": "Adjective", "s": "Adjective", "r": "Adverb"}
    pos = pos_map.get(synsets[0].pos(), None)
    synonyms = set()
    for synset in synsets:
        for lemma in synset.lemmas():
            name = lemma.name().replace("_", " ")
            if name.lower() != word.lower():
                synonyms.add(name)
    return {"pos": pos, "synonyms": sorted(synonyms)}


def _prefer_synonyms(word: str, candidates: list[str], pooled_words: set[str], limit: int = 3) -> list[str]:
    normalized_pool = {w.lower(): w for w in pooled_words}
    preferred = []
    fallback = []
    seen = set()

    for candidate in candidates:
        key = candidate.lower()
        if key in seen or key == word.lower():
            continue
        seen.add(key)
        if key in normalized_pool:
            preferred.append(normalized_pool[key])
        else:
            fallback.append(candidate)

    result = preferred[:limit]
    if len(result) < limit:
        result.extend(fallback[: limit - len(result)])
    return result


def _openai_client():
    try:
        from openai import OpenAI
    except Exception:
        return None
    return OpenAI()


def _call_openai(word: str, model: str) -> dict[str, Any]:
    client = _openai_client()
    if client is None:
        return {}

    prompt = (
        "You are a GRE vocabulary tutor. Return JSON with keys: "
        "meaning, pos, synonyms (list of 3), example, mnemonics (list of 1-2). "
        f"Word: {word}. Keep example sentence concise."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    content = response.choices[0].message.content
    if not content:
        return {}
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def enrich_entry(
    entry: WordEntry,
    pooled_words: set[str],
    cache: dict[str, Any],
    config: EnrichmentConfig,
    call_counter: dict[str, int],
) -> WordEntry:
    key = entry.word.lower()
    cached = cache.get(key, {})

    if config.enrich_only_when_missing:
        needs = any(
            [
                not entry.meaning,
                not entry.example,
                not entry.pos,
                not entry.mnemonics,
                not entry.synonyms,
            ]
        )
    else:
        needs = True

    if not needs:
        return entry

    wordnet_data = cached.get("wordnet") or _wordnet_lookup(entry.word)
    cached["wordnet"] = wordnet_data

    synonyms = entry.synonyms or []
    synonyms = _prefer_synonyms(entry.word, synonyms, pooled_words, limit=3)

    if len(synonyms) < 3:
        wn_syns = wordnet_data.get("synonyms", [])
        synonyms = _prefer_synonyms(entry.word, synonyms + wn_syns, pooled_words, limit=3)

    if not entry.pos and wordnet_data.get("pos"):
        entry.pos = wordnet_data["pos"]

    openai_data: dict[str, Any] = cached.get("openai", {})
    if config.enable_openai and call_counter["count"] < config.max_calls_per_run:
        if not openai_data or not config.enrich_only_when_missing:
            attempts = 0
            while attempts < 3:
                try:
                    openai_data = _call_openai(entry.word, config.openai_model)
                    call_counter["count"] += 1
                    break
                except Exception:
                    attempts += 1
                    time.sleep(2**attempts)
            cached["openai"] = openai_data

    if openai_data:
        if not entry.meaning and openai_data.get("meaning"):
            entry.meaning = str(openai_data["meaning"]).strip()
        if not entry.pos and openai_data.get("pos"):
            entry.pos = str(openai_data["pos"]).strip()
        if not entry.example and openai_data.get("example"):
            entry.example = str(openai_data["example"]).strip()
        if not entry.mnemonics and openai_data.get("mnemonics"):
            entry.mnemonics = [str(item).strip() for item in openai_data["mnemonics"]][:2]
        if len(synonyms) < 3 and openai_data.get("synonyms"):
            synonyms = _prefer_synonyms(
                entry.word,
                synonyms + list(openai_data["synonyms"]),
                pooled_words,
                limit=3,
            )

    entry.synonyms = synonyms
    cache[key] = cached
    return entry
