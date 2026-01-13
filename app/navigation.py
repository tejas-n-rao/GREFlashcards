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
        st.markdown(
            """
            <div class="sidebar-card">
              <div class="sidebar-title">GRE Vocab Studio</div>
              <p class="sidebar-caption">Immersive, offline-first flashcards</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _nav_buttons()
