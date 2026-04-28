from __future__ import annotations

import html
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components

path = Path(__file__).resolve()
repo_root = path.parents[2] if path.parent.name == "pages" else path.parents[1]
sys.path.insert(0, str(repo_root))

from app.navigation import render_nav
from app.state import ensure_state, save_deck_progress_state
from app.ui import apply_theme
from config import (
    DECK_MAX_REVIEW_PER_SESSION,
    DECK_MIX_NEW_AND_REVIEW,
    DECK_NEW_WORDS_PER_SESSION,
    DECK_OPEN_MODE,
    DECK_UNLOCK_THRESHOLD,
)
from core.deck_progress import DeckSessionSettings, build_deck_session, deck_progress_counts


st.set_page_config(page_title="Deck Progress", layout="wide")
apply_theme()
render_nav()
ensure_state()

st.markdown(
    """
    <div class="hero">
      <div class="hero-title">Deck Progress</div>
      <div class="hero-subtitle">Climb deck by deck with review-first sessions.</div>
      <div class="hero-tags">
        <span class="pill">Deck-wise</span>
        <span class="pill">Review due</span>
        <span class="pill">Session builder</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

decks = st.session_state.custom_decks
if not decks:
    st.info("Create decks in Custom Decks to start tracking progress.")
    st.stop()

st.markdown(
    """
    <style>
      .deck-card.deck-selected { outline: 2px solid rgba(176, 124, 255, 0.75); box-shadow: 0 0 0 3px rgba(176, 124, 255, 0.2); }
      .deck-meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem; }
      .deck-stat { background: var(--panel-strong); padding: 0.6rem 0.8rem; border-radius: 12px; border: 1px solid rgba(173, 128, 255, 0.24); }
      .deck-stat .label { color: var(--muted); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; }
      .deck-stat .value { font-size: 1.2rem; font-weight: 600; margin-top: 0.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

search_query = st.text_input("Search decks", placeholder="Search decks", key="deck_search")

deck_names = list(decks.keys())
filtered = [name for name in deck_names if search_query.lower() in name.lower()]
if not filtered:
    st.info("No decks match that search.")
    st.stop()

deck_settings = st.session_state.deck_settings
deck_states = st.session_state.deck_progress
deck_stats = st.session_state.stats
now = datetime.now()

def _settings_for(deck_id: str) -> DeckSessionSettings:
    settings = deck_settings.get(deck_id)
    if settings:
        return settings
    default_new = int(deck_stats.get("deck_new_words_per_session", DECK_NEW_WORDS_PER_SESSION))
    default_review = int(deck_stats.get("deck_max_review_per_session", DECK_MAX_REVIEW_PER_SESSION))
    default_mix = bool(deck_stats.get("deck_mix_new_and_review", DECK_MIX_NEW_AND_REVIEW))
    settings = DeckSessionSettings(
        new_words_per_session=default_new,
        max_review_per_session=default_review,
        mix_new_and_review=default_mix,
    )
    deck_settings[deck_id] = settings
    return settings


def _completion_ratio(counts: dict[str, int], total: int) -> float:
    if total == 0:
        return 0.0
    return (counts.get("review", 0) + counts.get("mastered", 0)) / total


open_mode = deck_stats.get("deck_open_mode", DECK_OPEN_MODE)
unlocked = set(filtered)
if open_mode != "open":
    unlocked = set()
    for idx, name in enumerate(filtered):
        if idx == 0:
            unlocked.add(name)
            continue
        prev = filtered[idx - 1]
        prev_words = decks.get(prev, [])
        prev_ids = [entry.word for entry in prev_words]
        prev_counts = deck_progress_counts(prev_ids, deck_states.get(prev, {}), now)
        if _completion_ratio(prev_counts, len(prev_ids)) >= DECK_UNLOCK_THRESHOLD:
            unlocked.add(name)
        else:
            break

for idx, deck_name in enumerate(filtered):
    words = decks.get(deck_name, [])
    word_ids = [entry.word for entry in words]
    total = len(word_ids)
    counts = deck_progress_counts(word_ids, deck_states.get(deck_name, {}), now)
    mastered_pct = int(round((counts["mastered"] / total) * 100)) if total else 0
    due_count = counts["due"]

    st.markdown(
        f"<div class='card deck-card' data-deck-index='{idx}'><h3>{html.escape(deck_name)}</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p><strong>Total words:</strong> {total} | <strong>Due now:</strong> {due_count} | "
        f"<strong>Mastered %:</strong> {mastered_pct}%</p>",
        unsafe_allow_html=True,
    )
    stats_html = "".join(
        [
            f"<div class='deck-stat'><div class='label'>New</div><div class='value'>{counts['new']}</div></div>",
            f"<div class='deck-stat'><div class='label'>Learning</div><div class='value'>{counts['learning']}</div></div>",
            f"<div class='deck-stat'><div class='label'>Review</div><div class='value'>{counts['review']}</div></div>",
            f"<div class='deck-stat'><div class='label'>Mastered</div><div class='value'>{counts['mastered']}</div></div>",
        ]
    )
    st.markdown(f"<div class='deck-meta'>{stats_html}</div>", unsafe_allow_html=True)

    locked = deck_name not in unlocked
    settings = _settings_for(deck_name)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Study Deck", key=f"study-{deck_name}", use_container_width=True, disabled=locked):
            session_words = build_deck_session(
                word_ids, deck_states.get(deck_name, {}), settings, now, review_only=False
            )
            if not session_words:
                st.warning("No cards available for a study session.")
            else:
                st.session_state.deck_session = {
                    "sessionId": uuid4().hex,
                    "source": "deck",
                    "deckId": deck_name,
                    "wordIds": session_words,
                }
                st.session_state.deck_queue = session_words
                st.session_state.deck_results = []
                save_deck_progress_state()
                st.switch_page("pages/Study.py")
    with col_b:
        if st.button(
            "Review Due",
            key=f"review-{deck_name}",
            use_container_width=True,
            disabled=locked or due_count == 0,
        ):
            session_words = build_deck_session(
                word_ids, deck_states.get(deck_name, {}), settings, now, review_only=True
            )
            if not session_words:
                st.warning("No due cards in this deck.")
            else:
                st.session_state.deck_session = {
                    "sessionId": uuid4().hex,
                    "source": "deck",
                    "deckId": deck_name,
                    "wordIds": session_words,
                }
                st.session_state.deck_queue = session_words
                st.session_state.deck_results = []
                save_deck_progress_state()
                st.switch_page("pages/Study.py")

    if locked:
        st.info("Complete the previous deck to unlock this one.")
    st.markdown("</div>", unsafe_allow_html=True)

components.html(
    """
    <script>
      (function () {
        if (window.__deckShortcutsInstalled) return;
        window.__deckShortcutsInstalled = true;
        const doc = window.parent ? window.parent.document : document;
        const selectedClass = "deck-selected";
        const modalId = "deck-shortcuts-modal";

        function deckCards() {
          return Array.from(doc.querySelectorAll(".deck-card"));
        }

        function highlight(index) {
          const cards = deckCards();
          cards.forEach((card, idx) => {
            if (idx === index) card.classList.add(selectedClass);
            else card.classList.remove(selectedClass);
          });
        }

        function clickButton(label, index) {
          const buttons = Array.from(doc.querySelectorAll("button"));
          const matches = buttons.filter((btn) => btn.innerText.trim() === label);
          if (matches[index]) matches[index].click();
        }

        function openModal() {
          let modal = doc.getElementById(modalId);
          if (!modal) {
            modal = doc.createElement("div");
            modal.id = modalId;
            modal.innerHTML = `
              <div class="deck-modal-backdrop"></div>
              <div class="deck-modal">
                <h3>Deck Shortcuts</h3>
                <div class="row"><span class="key">J/K</span><span>Navigate decks</span></div>
                <div class="row"><span class="key">Enter</span><span>Study deck</span></div>
                <div class="row"><span class="key">S</span><span>Study deck</span></div>
                <div class="row"><span class="key">R</span><span>Review due</span></div>
                <div class="row"><span class="key">/</span><span>Search decks</span></div>
                <div class="row"><span class="key">Esc</span><span>Close modal</span></div>
              </div>
            `;
            const style = doc.createElement("style");
            style.textContent = `
              #${modalId} { position: fixed; inset: 0; z-index: 9999; display: none; }
              #${modalId}.open { display: block; }
              #${modalId} .deck-modal-backdrop { position: absolute; inset: 0; background: rgba(5, 2, 12, 0.75); }
              #${modalId} .deck-modal { position: relative; max-width: 420px; margin: 12vh auto; background: rgba(28, 14, 55, 0.95); padding: 1.5rem; border-radius: 18px; border: 1px solid rgba(176, 124, 255, 0.35); color: #f4efff; }
              #${modalId} .row { display: flex; justify-content: space-between; padding: 0.35rem 0; }
              #${modalId} .key { font-weight: 700; }
            `;
            doc.body.appendChild(style);
            doc.body.appendChild(modal);
            modal.querySelector(".deck-modal-backdrop").addEventListener("click", () => {
              modal.classList.remove("open");
            });
          }
          modal.classList.add("open");
        }

        function closeModal() {
          const modal = doc.getElementById(modalId);
          if (modal) modal.classList.remove("open");
        }

        let selectedIndex = 0;
        highlight(selectedIndex);

        doc.addEventListener("keydown", (event) => {
          const tag = event.target && event.target.tagName ? event.target.tagName.toLowerCase() : "";
          if (tag === "input" || tag === "textarea" || tag === "select" || event.target.isContentEditable) {
            if (event.key === "Escape") closeModal();
            return;
          }
          const cards = deckCards();
          if (!cards.length) return;
          if (event.key === "ArrowDown" || event.key.toLowerCase() === "j") {
            selectedIndex = Math.min(cards.length - 1, selectedIndex + 1);
            highlight(selectedIndex);
            event.preventDefault();
          } else if (event.key === "ArrowUp" || event.key.toLowerCase() === "k") {
            selectedIndex = Math.max(0, selectedIndex - 1);
            highlight(selectedIndex);
            event.preventDefault();
          } else if (event.key === "Enter" || event.key.toLowerCase() === "s") {
            clickButton("Study Deck", selectedIndex);
          } else if (event.key.toLowerCase() === "r") {
            clickButton("Review Due", selectedIndex);
          } else if (event.key === "/") {
            const input = doc.querySelector('input[placeholder="Search decks"]');
            if (input) {
              input.focus();
              event.preventDefault();
            }
          } else if (event.key === "?") {
            openModal();
            event.preventDefault();
          } else if (event.key === "Escape") {
            closeModal();
          }
        });
      })();
    </script>
    """,
    height=0,
)
