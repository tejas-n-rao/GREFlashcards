from __future__ import annotations

import streamlit as st


CSS = """
<style>
:root {
  --ink: #1a1c1f;
  --muted: #59636f;
  --accent: #d86b4d;
  --accent-2: #2f6b5d;
  --paper: #f6f1e8;
  --card: rgba(255, 255, 255, 0.94);
}

html, body, [class*="css"]  {
  font-family: "Libre Baskerville", "Georgia", serif;
  color: var(--ink);
}

.stApp {
  background: radial-gradient(circle at 20% 15%, #f7ead8 0%, #f6f1e8 40%, #e7efe9 100%);
}

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #f6efe4 0%, #f0ece4 100%);
  border-right: 1px solid rgba(0,0,0,0.06);
}

section[data-testid="stSidebar"] .stButton > button {
  width: 100%;
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.08);
  background: #2a2d34;
  color: #f8f6f2;
  padding: 0.55rem 0.8rem;
  font-size: 0.9rem;
}

section[data-testid="stSidebar"] .stButton > button:hover {
  background: #1f232a;
  border-color: rgba(0,0,0,0.12);
}

.stButton > button {
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.08);
  background: #2a2d34;
  color: #f8f6f2;
  padding: 0.5rem 0.9rem;
}

.stButton > button:hover {
  background: #1f232a;
}

.card {
  background: var(--card);
  border-radius: 20px;
  padding: 1.75rem;
  box-shadow: 0 12px 30px rgba(0,0,0,0.08);
  border: 1px solid rgba(0,0,0,0.06);
}

.word-title {
  font-size: 2.3rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  background: #efe3d4;
  color: #6d4c41;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.muted {
  color: var(--muted);
}

.section-title {
  font-variant: small-caps;
  letter-spacing: 0.08em;
  color: var(--muted);
}

hr {
  border: none;
  border-top: 1px solid rgba(0,0,0,0.08);
  margin: 1.2rem 0;
}
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
