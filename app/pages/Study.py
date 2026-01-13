from __future__ import annotations

from datetime import date
import sys
from pathlib import Path

import streamlit as st

path = Path(__file__).resolve()
repo_root = path.parents[2] if path.parent.name == "pages" else path.parents[1]
sys.path.insert(0, str(repo_root))

from app.navigation import render_nav
from app.state import ensure_review_state, ensure_state, save_progress_state
from app.ui import apply_theme
from config import EXTRA_CARDS_PER_SESSION, NEW_CARDS_PER_SESSION
from core.metrics import due_words
from core.scheduler import schedule_review


st.set_page_config(page_title="Study", layout="wide")
apply_theme()
render_nav()
ensure_state()

st.title("Study Session")

entries = st.session_state.entries
sets = st.session_state.sets
active_set = st.session_state.active_set

if not entries:
    st.info("No entries loaded yet. Rebuild the dataset on Home.")
    st.stop()

set_names = list(sets.keys())

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
sets_for_source = sorted(source_map[source_choice], key=_set_sort_key)

active_set = st.selectbox(
    "Set",
    options=sets_for_source,
    index=sets_for_source.index(active_set)
    if active_set in sets_for_source
    else 0,
)
st.session_state.active_set = active_set

word_list = sets[active_set].word_keys if active_set in sets else []

if "study_queue" not in st.session_state:
    st.session_state.study_queue = []

if st.button("Start Session"):
    due = due_words(word_list, st.session_state.progress)
    new_words = [word for word in word_list if word.lower() not in st.session_state.progress]
    extra = [word for word in word_list if word not in due and word not in new_words]

    queue = []
    queue.extend(due)
    queue.extend(new_words[:NEW_CARDS_PER_SESSION])
    queue.extend(extra[:EXTRA_CARDS_PER_SESSION])
    st.session_state.study_queue = queue

queue = st.session_state.study_queue

if not queue:
    st.info("Start a session to begin reviewing cards.")
    st.stop()

current_word = queue[0]
entry = next((item for item in entries if item.word.lower() == current_word.lower()), None)
if entry is None:
    st.warning("Word not found in dataset.")
    st.stop()

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown(f"<div class='word-title'>{entry.word}</div>", unsafe_allow_html=True)

pos_display = entry.pos or ""
if pos_display:
    st.markdown(f"<span class='badge'>{pos_display}</span>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>Meaning</div>", unsafe_allow_html=True)
st.write(entry.meaning or "—")

st.markdown("<div class='section-title'>Example</div>", unsafe_allow_html=True)
st.write(entry.example or "—")

st.markdown("<div class='section-title'>Synonyms</div>", unsafe_allow_html=True)
if entry.synonyms:
    st.write(", ".join(entry.synonyms[:3]))
else:
    st.write("—")

st.markdown("<div class='section-title'>Mnemonics</div>", unsafe_allow_html=True)
if entry.mnemonics:
    st.write("; ".join(entry.mnemonics[:2]))
else:
    st.write("—")

st.markdown("<div class='section-title'>Source</div>", unsafe_allow_html=True)
source_lines = []
for source in entry.sources:
    label = f"{source.filename} / {source.sheet}"
    if source.subcategory:
        label += f" / {source.subcategory}"
    source_lines.append(label)
st.write("; ".join(source_lines) if source_lines else "—")

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

rating = None
if col1.button("Again"):
    rating = "again"
if col2.button("Hard"):
    rating = "hard"
if col3.button("Good"):
    rating = "good"
if col4.button("Easy"):
    rating = "easy"

if rating:
    state = ensure_review_state(entry.word)
    st.session_state.progress[entry.word.lower()] = schedule_review(state, rating)
    st.session_state.study_queue = queue[1:]
    st.session_state.stats["last_review_date"] = date.today().isoformat()
    save_progress_state()
    st.rerun()
