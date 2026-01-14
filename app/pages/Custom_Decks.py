from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

path = Path(__file__).resolve()
repo_root = path.parents[2] if path.parent.name == "pages" else path.parents[1]
sys.path.insert(0, str(repo_root))

from app.navigation import render_nav
from app.state import ensure_state, refresh_sets_state, save_custom_decks_state
from app.ui import apply_theme
from core.custom_decks import CUSTOM_SOURCE, parse_list_field
from core.models import SourceRef, WordEntry


st.set_page_config(page_title="Custom Decks", layout="wide")
apply_theme()
render_nav()
ensure_state()

st.markdown(
    """
    <div class="hero">
      <div class="hero-title">Custom Decks</div>
      <div class="hero-subtitle">Build your own flashcard sets for targeted practice.</div>
      <div class="hero-tags">
        <span class="pill">Personalized</span>
        <span class="pill">Fast capture</span>
        <span class="pill">Study-ready</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

decks: dict[str, list[WordEntry]] = st.session_state.custom_decks

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("### Create a New Deck")
new_deck_name = st.text_input("Deck name", key="new_deck_name")
if st.button("Create Deck", use_container_width=True):
    name = new_deck_name.strip()
    if not name:
        st.warning("Enter a deck name to continue.")
    elif name in decks:
        st.warning("That deck already exists.")
    else:
        decks[name] = []
        st.session_state.new_deck_name = ""
        save_custom_decks_state()
        refresh_sets_state()
        st.success(f"Created deck: {name}")
st.markdown("</div>", unsafe_allow_html=True)

if not decks:
    st.info("Create your first deck to start adding cards.")
    st.stop()

deck_names = list(decks.keys())
selected_deck = st.selectbox("Choose deck", options=deck_names)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("### Add a Card")
with st.form("add_card_form", clear_on_submit=True):
    word = st.text_input("Word")
    meaning = st.text_area("Meaning")
    example = st.text_area("Example sentence")
    pos = st.text_input("Part of speech")
    synonyms_raw = st.text_input("Synonyms (comma-separated)")
    mnemonics_raw = st.text_input("Mnemonics (comma-separated)")
    tags_raw = st.text_input("Tags (comma-separated)")
    submitted = st.form_submit_button("Add Card")

if submitted:
    cleaned_word = word.strip()
    if not cleaned_word:
        st.warning("Word is required.")
    else:
        existing = {entry.word.lower() for entry in decks[selected_deck]}
        if cleaned_word.lower() in existing:
            st.warning("That word is already in this deck.")
        else:
            decks[selected_deck].append(
                WordEntry(
                    word=cleaned_word,
                    meaning=meaning.strip() or None,
                    example=example.strip() or None,
                    pos=pos.strip() or None,
                    synonyms=parse_list_field(synonyms_raw),
                    mnemonics=parse_list_field(mnemonics_raw),
                    tags=parse_list_field(tags_raw),
                    sources=[SourceRef(filename=CUSTOM_SOURCE, sheet=selected_deck)],
                )
            )
            save_custom_decks_state()
            refresh_sets_state()
            st.success(f"Added {cleaned_word} to {selected_deck}.")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("### Deck Preview")
deck_cards = decks.get(selected_deck, [])
st.markdown(f"**Total cards:** {len(deck_cards)}")

if deck_cards:
    preview_rows = [
        {
            "Word": entry.word,
            "Meaning": entry.meaning or "",
            "POS": entry.pos or "",
            "Synonyms": ", ".join(entry.synonyms),
        }
        for entry in deck_cards
    ]
    st.dataframe(preview_rows, use_container_width=True, hide_index=True)
else:
    st.info("No cards in this deck yet.")
st.markdown("</div>", unsafe_allow_html=True)
