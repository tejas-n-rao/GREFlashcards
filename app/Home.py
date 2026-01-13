from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

path = Path(__file__).resolve()
repo_root = path.parents[2] if path.parent.name == "pages" else path.parents[1]
sys.path.insert(0, str(repo_root))

from config import EXCEL_FILES
from core.data_manager import enrich_entries
from core.sets import build_sets
from app.navigation import render_nav
from app.state import ensure_state, rebuild_dataset, save_normalized_state
from app.ui import apply_theme


st.set_page_config(page_title="GRE Vocab Studio", layout="wide")
apply_theme()
render_nav()
ensure_state()

st.title("GRE Vocab Studio")
st.subheader("Normalization and Dataset Summary")

col_a, col_b = st.columns([1, 2])
with col_a:
    st.markdown("### Data Sources")
    for path in EXCEL_FILES:
        st.write(f"- {path}")

    if st.button("Rebuild Dataset"):
        rebuild_dataset()
        st.success("Dataset rebuilt from Excel sources.")

with col_b:
    report = st.session_state.report or {}
    st.markdown("### Normalization Report")
    st.json(report)

st.markdown("---")

st.markdown("### Enrichment")
col_c, col_d = st.columns([2, 1])
with col_c:
    st.write(
        "Run optional enrichment to fill missing meanings, POS, examples, synonyms, and mnemonics."
    )
with col_d:
    if st.button("Run Enrichment"):
        pooled = {entry.word for entry in st.session_state.entries}
        st.session_state.entries = enrich_entries(
            st.session_state.entries,
            pooled_words=pooled,
            enable_openai=st.session_state.get("enable_openai"),
            enrich_only_when_missing=st.session_state.get("enrich_only_when_missing"),
            max_calls_per_run=st.session_state.get("max_calls_per_run"),
        )
        st.session_state.sets = build_sets(st.session_state.entries)
        save_normalized_state()
        st.success("Enrichment complete.")

st.markdown("---")

st.markdown("### Next Steps")
st.info("Go to Study to start reviewing cards or use Dashboard to explore stats and search.")
