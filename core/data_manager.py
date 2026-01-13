from __future__ import annotations

from typing import Any

from config import (
    ENRICHMENT_CACHE_PATH,
    NORMALIZED_VOCAB_PATH,
    OPENAI_MODEL,
    ENABLE_OPENAI_ENRICHMENT,
    MAX_OPENAI_CALLS_PER_RUN,
    ENRICH_ONLY_WHEN_MISSING,
)
from core.enrichment import EnrichmentConfig, enrich_entry
from core.models import WordEntry
from core.normalization import normalize_excel_files
from core.persistence import load_cache, load_normalized, save_cache, save_normalized


def build_normalized_dataset(excel_files: list[str]) -> tuple[list[WordEntry], dict[str, Any]]:
    entries, report = normalize_excel_files(excel_files)
    save_normalized(NORMALIZED_VOCAB_PATH, entries, report)
    return entries, report.to_dict()


def load_or_build(excel_files: list[str]) -> tuple[list[WordEntry], dict[str, Any]]:
    entries, report = load_normalized(NORMALIZED_VOCAB_PATH)
    if not entries:
        entries, report = build_normalized_dataset(excel_files)
    return entries, report


def enrich_entries(
    entries: list[WordEntry],
    pooled_words: set[str],
    enable_openai: bool | None = None,
    enrich_only_when_missing: bool | None = None,
    max_calls_per_run: int | None = None,
) -> list[WordEntry]:
    cache = load_cache(ENRICHMENT_CACHE_PATH)

    config = EnrichmentConfig(
        enable_openai=ENABLE_OPENAI_ENRICHMENT if enable_openai is None else enable_openai,
        openai_model=OPENAI_MODEL,
        max_calls_per_run=MAX_OPENAI_CALLS_PER_RUN if max_calls_per_run is None else max_calls_per_run,
        enrich_only_when_missing=ENRICH_ONLY_WHEN_MISSING
        if enrich_only_when_missing is None
        else enrich_only_when_missing,
    )

    call_counter = {"count": 0}
    updated = []
    for entry in entries:
        updated.append(enrich_entry(entry, pooled_words, cache, config, call_counter))
    save_cache(ENRICHMENT_CACHE_PATH, cache)
    return updated
