from __future__ import annotations

import streamlit as st


def _nav_buttons() -> None:
    pages = {
        "Home": "Home.py",
        "Study": "pages/Study.py",
        "Dashboard": "pages/Dashboard.py",
        "Word Detail": "pages/Word_Detail.py",
        "Settings": "pages/Settings.py",
    }

    for label, page in pages.items():
        if st.button(label, use_container_width=True):
            st.switch_page(page)


def render_nav() -> None:
    with st.sidebar:
        st.header("GRE Vocab Studio")
        st.caption("Aesthetic, offline-first flashcards")
        _nav_buttons()
