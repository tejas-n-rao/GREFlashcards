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

report = st.session_state.report or {}
entries = st.session_state.entries

st.markdown(
    """
    <div class="hero">
      <div class="hero-title">GRE Vocab Studio</div>
      <div class="hero-subtitle">Curate, enrich, and rehearse vocabulary with precision.</div>
      <div class="hero-tags">
        <span class="pill">Dark Purple</span>
        <span class="pill">Offline-first</span>
        <span class="pill">Spaced repetition</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

def _stat_card(label: str, value: str) -> str:
    return (
        "<div class='stat-card'>"
        f"<div class='stat-label'>{label}</div>"
        f"<div class='stat-value'>{value}</div>"
        "</div>"
    )

total_rows = report.get("total_rows", 0)
total_words = report.get("total_words", len(entries))
deduped_words = report.get("deduped_words", len(entries))
missing_meaning = report.get("missing_meaning", 0)

stat_html = "".join(
    [
        _stat_card("Total rows", f"{total_rows:,}"),
        _stat_card("Unique words", f"{deduped_words:,}"),
        _stat_card("Source words", f"{total_words:,}"),
        _stat_card("Missing meaning", f"{missing_meaning:,}"),
    ]
)
st.markdown(f"<div class='stat-grid'>{stat_html}</div>", unsafe_allow_html=True)

col_a, col_b = st.columns([1, 2])
with col_a:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### Data Sources")
    for path in EXCEL_FILES:
        st.write(f"- {path}")

    if st.button("Rebuild Dataset"):
        rebuild_dataset()
        st.success("Dataset rebuilt from Excel sources.")
    st.markdown("</div>", unsafe_allow_html=True)

with col_b:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### Normalization Report")
    st.json(report)
    missing_files = report.get("missing_files", [])
    if missing_files:
        st.warning("Some Excel files were not found. Check config.py paths.")
        for path in missing_files:
            st.code(path)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
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
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("### Next Steps")
st.info("Go to Study to start reviewing cards or use Dashboard to explore stats and search.")
st.markdown("</div>", unsafe_allow_html=True)
