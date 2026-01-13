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
    ENABLE_OPENAI_ENRICHMENT,
    ENRICH_ONLY_WHEN_MISSING,
    MAX_OPENAI_CALLS_PER_RUN,
)


st.set_page_config(page_title="Settings", layout="wide")
apply_theme()
render_nav()
ensure_state()

st.title("Settings")

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

st.markdown("---")

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
