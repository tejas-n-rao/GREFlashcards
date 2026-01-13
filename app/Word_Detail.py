from __future__ import annotations

import streamlit as st

from app.navigation import render_nav
from app.state import ensure_state, save_normalized_state
from app.ui import apply_theme
from config import (
    ENABLE_OPENAI_ENRICHMENT,
    ENRICH_ONLY_WHEN_MISSING,
    ENRICHMENT_CACHE_PATH,
    MAX_OPENAI_CALLS_PER_RUN,
    OPENAI_MODEL,
)
from core.enrichment import EnrichmentConfig, enrich_entry
from core.persistence import load_cache, save_cache
from core.word_ops import entry_map


st.set_page_config(page_title="Word Detail", layout="wide")
apply_theme()
render_nav()
ensure_state()

entries = st.session_state.entries
index = entry_map(entries)

st.title("Word Detail")

if not entries:
    st.info("No entries loaded yet. Rebuild the dataset on Home.")
    st.stop()

selected = st.session_state.get("selected_word")
options = sorted([entry.word for entry in entries])
default_index = 0
if selected:
    try:
        default_index = options.index(selected)
    except ValueError:
        lower_map = {value.lower(): idx for idx, value in enumerate(options)}
        default_index = lower_map.get(selected.lower(), 0)

word = st.selectbox("Select word", options=options, index=default_index)
entry = index.get(word.lower())
if not entry:
    st.warning("Word not found.")
    st.stop()

st.markdown("---")

col_a, col_b = st.columns(2)
with col_a:
    meaning = st.text_area("Meaning", value=entry.meaning or "")
    example = st.text_area("Example", value=entry.example or "")
    pos = st.text_input("Part of Speech", value=entry.pos or "")

with col_b:
    synonyms = st.text_input("Synonyms (comma-separated)", value=", ".join(entry.synonyms))
    mnemonics = st.text_area("Mnemonics (1-2, separated by newlines)", value="\n".join(entry.mnemonics))
    tags = st.text_input("Tags (comma-separated)", value=", ".join(entry.tags))

st.markdown("### Sources")
source_lines = []
for source in entry.sources:
    label = f"{source.filename} / {source.sheet}"
    if source.subcategory:
        label += f" / {source.subcategory}"
    source_lines.append(label)

st.write("; ".join(source_lines) if source_lines else "—")

if st.button("Save Changes"):
    entry.meaning = meaning.strip() or None
    entry.example = example.strip() or None
    entry.pos = pos.strip() or None
    entry.synonyms = [item.strip() for item in synonyms.split(",") if item.strip()]
    entry.mnemonics = [item.strip() for item in mnemonics.split("\n") if item.strip()]
    entry.tags = [item.strip() for item in tags.split(",") if item.strip()]

    save_normalized_state()
    st.success("Saved.")

if ENABLE_OPENAI_ENRICHMENT and st.button("Generate/Refresh Enrichment"):
    pooled = {item.word for item in entries}
    cache = load_cache(ENRICHMENT_CACHE_PATH)
    config = EnrichmentConfig(
        enable_openai=st.session_state.get("enable_openai", ENABLE_OPENAI_ENRICHMENT),
        openai_model=OPENAI_MODEL,
        max_calls_per_run=st.session_state.get("max_calls_per_run", MAX_OPENAI_CALLS_PER_RUN),
        enrich_only_when_missing=st.session_state.get(
            "enrich_only_when_missing", ENRICH_ONLY_WHEN_MISSING
        ),
    )
    entry = enrich_entry(entry, pooled, cache, config, {"count": 0})
    save_cache(ENRICHMENT_CACHE_PATH, cache)
    save_normalized_state()
    st.success("Enrichment updated.")
