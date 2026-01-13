from __future__ import annotations

from datetime import date
import html
import random
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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

st.markdown(
    """
    <div class="hero">
      <div class="hero-title">Study Session</div>
      <div class="hero-subtitle">Focus on the words that matter most right now.</div>
      <div class="hero-tags">
        <span class="pill">Daily review</span>
        <span class="pill">Adaptive queue</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

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
if "shuffle_sets" not in st.session_state:
    st.session_state.shuffle_sets = False
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

total_cards = len(word_list)
correct_cards = 0
wrong_cards = 0
remaining_cards = 0
for word in word_list:
    state = st.session_state.progress.get(word.lower())
    if not state or state.review_count == 0:
        remaining_cards += 1
        continue
    if state.correct_count >= state.incorrect_count:
        correct_cards += 1
    else:
        wrong_cards += 1

def _percent(value: int, total: int) -> int:
    if total == 0:
        return 0
    return int(round((value / total) * 100))

correct_pct = _percent(correct_cards, total_cards)
wrong_pct = _percent(wrong_cards, total_cards)
remaining_pct = max(0, 100 - correct_pct - wrong_pct)

st.markdown("### Set Progress")
bar_html = (
    "<div class='master-bar'>"
    f"<div class='bar-segment bar-green' style='width:{correct_pct}%;'>{correct_pct}%</div>"
    f"<div class='bar-segment bar-red' style='width:{wrong_pct}%;'>{wrong_pct}%</div>"
    f"<div class='bar-segment bar-white' style='width:{remaining_pct}%;'>{remaining_pct}%</div>"
    "</div>"
)
st.markdown(bar_html, unsafe_allow_html=True)
st.markdown(
    f"<div class='bar-caption'>"
    f"<span>Right: {correct_cards}</span>"
    f"<span>Wrong: {wrong_cards}</span>"
    f"<span>Unseen: {remaining_cards}</span>"
    f"<span>Total: {total_cards}</span>"
    f"</div>",
    unsafe_allow_html=True,
)
st.session_state.shuffle_sets = st.checkbox(
    "Shuffle fixed sets for this session",
    value=st.session_state.shuffle_sets,
)

confirm_reset = st.checkbox("Confirm reset progress for this set", value=False)
if st.button("Reset progress for this set", use_container_width=True, disabled=not confirm_reset):
    for word in word_list:
        st.session_state.progress.pop(word.lower(), None)
    st.session_state.study_queue = []
    save_progress_state()
    st.success("Progress reset for this set.")

if st.button("Start Session", use_container_width=True):
    set_words = list(word_list)
    if st.session_state.shuffle_sets and not active_set.startswith("Pooled"):
        random.shuffle(set_words)
    due = due_words(set_words, st.session_state.progress)
    new_words = [word for word in set_words if word.lower() not in st.session_state.progress]
    extra = [word for word in set_words if word not in due and word not in new_words]

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

st.markdown("<div class='card flashcard'>", unsafe_allow_html=True)
st.markdown(f"<div class='word-title'>{html.escape(entry.word)}</div>", unsafe_allow_html=True)

pos_display = entry.pos or ""
if pos_display:
    st.markdown(f"<span class='badge'>{html.escape(pos_display)}</span>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

source_lines = []
for source in entry.sources:
    label = f"{source.filename} / {source.sheet}"
    if source.subcategory:
        label += f" / {source.subcategory}"
    source_lines.append(label)

def _flash_item(title: str, body: str) -> str:
    safe_body = html.escape(body) if body else "—"
    return (
        "<div class='flash-item'>"
        f"<div class='section-title'>{html.escape(title)}</div>"
        f"<p>{safe_body}</p>"
        "</div>"
    )

flash_html = "".join(
    [
        _flash_item("Meaning", entry.meaning or ""),
        _flash_item("Example", entry.example or ""),
        _flash_item("Synonyms", ", ".join(entry.synonyms[:3]) if entry.synonyms else ""),
        _flash_item("Mnemonics", "; ".join(entry.mnemonics[:2]) if entry.mnemonics else ""),
    ]
)
st.markdown(f"<div class='flash-grid'>{flash_html}</div>", unsafe_allow_html=True)
source_note = html.escape("; ".join(source_lines) if source_lines else "—")
st.markdown(
    f"<div class='flash-note'><span class='section-title'>Source</span> {source_note}</div>",
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

rating = None
if col1.button("Again", use_container_width=True):
    rating = "again"
if col2.button("Hard", use_container_width=True):
    rating = "hard"
if col3.button("Good", use_container_width=True):
    rating = "good"
if col4.button("Easy", use_container_width=True):
    rating = "easy"

if rating:
    state = ensure_review_state(entry.word)
    st.session_state.progress[entry.word.lower()] = schedule_review(state, rating)
    st.session_state.study_queue = queue[1:]
    st.session_state.stats["last_review_date"] = date.today().isoformat()
    save_progress_state()
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

components.html(
    """
    <script>
      (function () {
        if (window.__greShortcutsInstalled) return;
        window.__greShortcutsInstalled = true;
        const keyMap = {
          "a": "Again",
          "h": "Hard",
          "g": "Good",
          "e": "Easy",
          "s": "Start Session"
        };
        const handler = (event) => {
          const tag = (event.target && event.target.tagName) ? event.target.tagName.toLowerCase() : "";
          if (tag === "input" || tag === "textarea" || tag === "select" || event.target.isContentEditable) {
            return;
          }
          const key = event.key.toLowerCase();
          if (!keyMap[key]) return;
          const doc = window.parent ? window.parent.document : document;
          const buttons = Array.from(doc.querySelectorAll("button"));
          const target = buttons.find(btn => btn.innerText.trim() === keyMap[key]);
          if (target) {
            target.click();
          }
        };
        document.addEventListener("keydown", handler);
        if (window.parent && window.parent.document) {
          window.parent.document.addEventListener("keydown", handler);
        }
      })();
    </script>
    """,
    height=0,
)

st.markdown(
    """
    <details class="shortcut-legend">
      <summary>⌨</summary>
      <div class="shortcut-panel">
        <h4>Shortcuts</h4>
        <div class="row"><span class="shortcut-key">A</span><span>Again</span></div>
        <div class="row"><span class="shortcut-key">H</span><span>Hard</span></div>
        <div class="row"><span class="shortcut-key">G</span><span>Good</span></div>
        <div class="row"><span class="shortcut-key">E</span><span>Easy</span></div>
        <div class="row"><span class="shortcut-key">S</span><span>Start Session</span></div>
      </div>
    </details>
    """,
    unsafe_allow_html=True,
)
