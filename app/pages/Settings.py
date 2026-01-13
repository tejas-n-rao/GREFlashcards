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

set_names = list(st.session_state.sets.keys())
active = st.selectbox(
    "Active Set",
    options=set_names,
    index=set_names.index(st.session_state.active_set)
    if st.session_state.active_set in set_names
    else set_names.index(DEFAULT_ACTIVE_SET)
    if DEFAULT_ACTIVE_SET in set_names
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
