from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

path = Path(__file__).resolve()
repo_root = path.parents[2] if path.parent.name == "pages" else path.parents[1]
sys.path.insert(0, str(repo_root))

from app.navigation import render_nav
from app.state import ensure_state, save_progress_state
from app.ui import apply_theme
from config import (
    DEFAULT_ACTIVE_SET,
    DECK_MAX_REVIEW_PER_SESSION,
    DECK_MIX_NEW_AND_REVIEW,
    DECK_NEW_WORDS_PER_SESSION,
    DECK_OPEN_MODE,
    ENABLE_OPENAI_ENRICHMENT,
    ENRICH_ONLY_WHEN_MISSING,
    MAX_OPENAI_CALLS_PER_RUN,
)


st.set_page_config(page_title="Settings", layout="wide")
apply_theme()
render_nav()
ensure_state()

st.markdown(
    """
    <div class="hero">
      <div class="hero-title">Settings</div>
      <div class="hero-subtitle">Control sources, active sets, and enrichment limits.</div>
      <div class="hero-tags">
        <span class="pill">Config</span>
        <span class="pill">Session</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

set_map = st.session_state.sets
set_names = list(set_map.keys())

def _set_sort_key(name: str) -> tuple[int, int, str]:
    if name.startswith("Pooled :: Set "):
        number = int(name.split("Set ")[1])
        return (3, number, name)
    if name == "Pooled":
        return (2, 0, name)
    if " :: Set " in name:
        base, _, tail = name.partition(" :: Set ")
        return (1, int(tail), base)
    if " :: " in name and "occur" in name.lower():
        parts = name.split(" :: ")
        freq = parts[-1]
        digits = "".join(ch for ch in freq if ch.isdigit())
        return (0, int(digits) if digits else 99, name)
    return (0, 0, name)

source_map: dict[str, list[str]] = {}
for name in set_names:
    if name == "Pooled" or name.startswith("Pooled ::"):
        source = "Pooled"
    elif " :: " in name:
        source = name.split(" :: ")[0]
    else:
        source = name
    source_map.setdefault(source, []).append(name)

sources = sorted(source_map.keys(), key=lambda s: (0, s) if s != "Pooled" else (1, s))
st.markdown("<div class='glass'>", unsafe_allow_html=True)
source_choice = st.selectbox("Source", options=sources)
set_names = sorted(source_map[source_choice], key=_set_sort_key)

def _display(name: str) -> str:
    count = len(set_map[name].word_keys)
    return f"{name} ({count} words)"

active = st.selectbox(
    "Set",
    options=set_names,
    format_func=_display,
    index=set_names.index(st.session_state.active_set)
    if st.session_state.active_set in set_names
    else 0,
)

st.session_state.active_set = active
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("Deck Defaults")
deck_stats = st.session_state.stats
deck_stats["deck_new_words_per_session"] = st.number_input(
    "New words per deck session",
    min_value=0,
    max_value=200,
    value=int(deck_stats.get("deck_new_words_per_session", DECK_NEW_WORDS_PER_SESSION)),
    step=5,
)
deck_stats["deck_max_review_per_session"] = st.number_input(
    "Max reviews per deck session",
    min_value=0,
    max_value=500,
    value=int(deck_stats.get("deck_max_review_per_session", DECK_MAX_REVIEW_PER_SESSION)),
    step=5,
)
deck_stats["deck_mix_new_and_review"] = st.checkbox(
    "Mix new and review cards",
    value=bool(deck_stats.get("deck_mix_new_and_review", DECK_MIX_NEW_AND_REVIEW)),
)
deck_stats["deck_open_mode"] = st.selectbox(
    "Deck access mode",
    options=["open", "gated"],
    index=0
    if deck_stats.get("deck_open_mode", DECK_OPEN_MODE) == "open"
    else 1,
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("Enrichment Options")
if not ENABLE_OPENAI_ENRICHMENT:
    st.info("OpenAI enrichment is disabled in config.py.")

st.session_state.enable_openai = st.checkbox(
    "Enable OpenAI for this session",
    value=st.session_state.get("enable_openai", ENABLE_OPENAI_ENRICHMENT),
    disabled=not ENABLE_OPENAI_ENRICHMENT,
)

st.session_state.enrich_only_when_missing = st.checkbox(
    "Only enrich missing fields",
    value=st.session_state.get("enrich_only_when_missing", ENRICH_ONLY_WHEN_MISSING),
)

st.session_state.max_calls_per_run = st.number_input(
    "Max OpenAI calls per run",
    min_value=0,
    max_value=1000,
    value=int(st.session_state.get("max_calls_per_run", MAX_OPENAI_CALLS_PER_RUN)),
    step=10,
)

if st.button("Save Settings"):
    save_progress_state()
    st.success("Settings saved.")
st.markdown("</div>", unsafe_allow_html=True)
