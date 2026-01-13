from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

path = Path(__file__).resolve()
repo_root = path.parents[2] if path.parent.name == "pages" else path.parents[1]
sys.path.insert(0, str(repo_root))

from app.navigation import render_nav
from app.state import ensure_state
from app.ui import apply_theme
from core.metrics import accuracy_for_words, due_words, weak_words
from core.word_ops import entry_map


st.set_page_config(page_title="Dashboard", layout="wide")
apply_theme()
render_nav()
ensure_state()

entries = st.session_state.entries
sets = st.session_state.sets
active_set = st.session_state.active_set

st.title("Dashboard")

if not entries:
    st.info("No entries loaded yet. Rebuild the dataset on Home.")
    st.stop()

active_words = sets[active_set].word_keys if active_set in sets else []
pooled_words = sets["Pooled"].word_keys if "Pooled" in sets else []

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("Due (Active Set)", len(due_words(active_words, st.session_state.progress)))
with col_b:
    st.metric("Due (Pooled)", len(due_words(pooled_words, st.session_state.progress)))
with col_c:
    accuracy = accuracy_for_words(pooled_words, st.session_state.progress)
    st.metric("Overall Accuracy", f"{accuracy:.0%}")

st.markdown("---")

col_d, col_e = st.columns([2, 1])
with col_d:
    st.subheader("Weak Words")
    weak_list = weak_words(entries, st.session_state.progress, limit=10)
    if not weak_list:
        st.write("No review history yet.")
    else:
        for word, acc in weak_list:
            st.write(f"{word} — {acc:.0%} accuracy")

with col_e:
    st.subheader("Search")
    query = st.text_input("Search word")
    if query:
        index = entry_map(entries)
        entry = index.get(query.lower())
        if entry:
            st.session_state.selected_word = entry.word
            st.success("Word found. Open Word Detail.")
        else:
            st.warning("No match found.")

st.markdown("---")

st.subheader("Set Accuracy")
set_names = list(sets.keys())
file_sets = [name for name in set_names if " :: " not in name and name != "Pooled"]
pooled_sets = [name for name in set_names if name.startswith("Pooled ::")]
chunk_sets = [name for name in set_names if " :: Set " in name and not name.startswith("Pooled")]

def _table(names: list[str]) -> list[dict[str, str]]:
    rows = []
    for set_name in names:
        words = sets[set_name].word_keys
        acc = accuracy_for_words(words, st.session_state.progress)
        rows.append({"set": set_name, "accuracy": f"{acc:.0%}", "count": len(words)})
    return rows

st.markdown("**Per-file Sets**")
st.dataframe(_table(file_sets), use_container_width=True)

st.markdown("**Per-file Chunks**")
st.dataframe(_table(chunk_sets), use_container_width=True)

st.markdown("**Pooled Chunks**")
st.dataframe(_table(pooled_sets), use_container_width=True)
