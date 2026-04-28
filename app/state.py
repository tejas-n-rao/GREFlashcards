from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st

from config import (
    CUSTOM_DECKS_PATH,
    DEFAULT_ACTIVE_SET,
    DECK_PROGRESS_PATH,
    EXCEL_FILES,
    PROGRESS_PATH,
)
from core.custom_decks import build_custom_sets, load_custom_decks, save_custom_decks
from core.data_manager import build_normalized_dataset, load_or_build
from core.models import ReviewState
from core.persistence import load_deck_progress, load_progress, save_deck_progress, save_progress, save_normalized
from core.models import NormalizationReport
from config import NORMALIZED_VOCAB_PATH
from core.scheduler import init_state
from core.sets import build_sets


def _refresh_sets() -> None:
    base_sets = build_sets(st.session_state.entries)
    custom_sets = build_custom_sets(st.session_state.custom_decks)
    merged = dict(base_sets)
    merged.update(custom_sets)
    st.session_state.custom_sets = custom_sets
    st.session_state.sets = merged


def ensure_state() -> None:
    if "entries" not in st.session_state:
        entries, report = load_or_build(EXCEL_FILES)
        st.session_state.entries = entries
        st.session_state.report = report

    if "custom_decks" not in st.session_state:
        st.session_state.custom_decks = load_custom_decks(CUSTOM_DECKS_PATH)

    if "sets" not in st.session_state:
        _refresh_sets()

    if "active_set" not in st.session_state:
        st.session_state.active_set = DEFAULT_ACTIVE_SET

    if "progress" not in st.session_state:
        states, stats = load_progress(PROGRESS_PATH)
        st.session_state.progress = states
        st.session_state.stats = stats

    if "deck_progress" not in st.session_state:
        deck_states, deck_settings = load_deck_progress(DECK_PROGRESS_PATH)
        st.session_state.deck_progress = deck_states
        st.session_state.deck_settings = deck_settings


def rebuild_dataset() -> None:
    entries, report = build_normalized_dataset(EXCEL_FILES)
    st.session_state.entries = entries
    st.session_state.report = report
    _refresh_sets()


def ensure_review_state(word: str) -> ReviewState:
    key = word.lower()
    states: dict[str, ReviewState] = st.session_state.progress
    if key not in states:
        states[key] = init_state(word)
    return states[key]


def save_progress_state() -> None:
    save_progress(PROGRESS_PATH, st.session_state.progress, st.session_state.stats)


def save_deck_progress_state() -> None:
    save_deck_progress(
        DECK_PROGRESS_PATH,
        st.session_state.deck_progress,
        st.session_state.deck_settings,
    )


def save_custom_decks_state() -> None:
    save_custom_decks(CUSTOM_DECKS_PATH, st.session_state.custom_decks)


def refresh_sets_state() -> None:
    _refresh_sets()


def update_last_session() -> None:
    stats: dict[str, Any] = st.session_state.stats
    stats["last_session"] = date.today().isoformat()


def save_normalized_state() -> None:
    report_data = st.session_state.report or {}
    if report_data:
        report = NormalizationReport(**report_data)
    else:
        report = NormalizationReport(
            total_rows=0,
            total_words=0,
            deduped_words=len(st.session_state.entries),
            missing_meaning=0,
            missing_example=0,
            missing_pos=0,
            missing_mnemonic=0,
            missing_synonyms=0,
            source_counts={},
            sheet_counts={},
        )
    save_normalized(NORMALIZED_VOCAB_PATH, st.session_state.entries, report)
