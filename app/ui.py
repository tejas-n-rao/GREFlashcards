from __future__ import annotations

import streamlit as st


CSS = """
<style>
:root {
  --ink: #1d1f2a;
  --accent: #ff6f3c;
  --accent-2: #1f7a8c;
  --paper: #f8f4ee;
  --card: rgba(255, 255, 255, 0.9);
  --muted: #5b617a;
}

html, body, [class*="css"]  {
  font-family: "Avenir Next", "Gill Sans", "Trebuchet MS", sans-serif;
  color: var(--ink);
}

.stApp {
  background: radial-gradient(circle at 10% 10%, #ffe8d2 0%, #f8f4ee 35%, #e9f2f6 100%);
}

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #faf0e6 0%, #f5f1ea 100%);
}

.card {
  background: var(--card);
  border-radius: 18px;
  padding: 1.5rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  border: 1px solid rgba(31, 122, 140, 0.1);
}

.word-title {
  font-size: 2.1rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  background: #f1d7c1;
  color: #6d4c41;
  font-size: 0.75rem;
  margin-right: 0.35rem;
}

.muted {
  color: var(--muted);
}

hr {
  border: none;
  border-top: 1px solid rgba(0,0,0,0.08);
  margin: 1rem 0;
}
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
