from __future__ import annotations

import streamlit as st


NAV_ITEMS = [
    ("Home", "app/Home.py"),
    ("Study", "app/Study.py"),
    ("Dashboard", "app/Dashboard.py"),
    ("Word Detail", "app/Word_Detail.py"),
    ("Settings", "app/Settings.py"),
]


def render_nav() -> None:
    with st.sidebar:
        st.header("GRE Vocab Studio")
        st.caption("Aesthetic, offline-first flashcards")
        for label, page in NAV_ITEMS:
            st.page_link(page, label=label)
