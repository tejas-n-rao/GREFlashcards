from __future__ import annotations

import streamlit as st


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Space+Grotesk:wght@400;500;600&display=swap');

:root {
  --bg-0: #0b0615;
  --bg-1: #140926;
  --bg-2: #1d0c36;
  --panel: rgba(27, 15, 55, 0.9);
  --panel-strong: rgba(36, 18, 73, 0.95);
  --panel-soft: rgba(21, 12, 38, 0.7);
  --ink: #f4efff;
  --muted: #b7a6d8;
  --accent: #b07cff;
  --accent-2: #ff78c8;
  --accent-3: #4de6d6;
  --stroke: rgba(178, 140, 255, 0.25);
  --glow: rgba(137, 86, 255, 0.35);
}

html, body, [class*="css"]  {
  font-family: "Space Grotesk", "Segoe UI", sans-serif;
  color: var(--ink);
}

h1, h2, h3, .hero-title, .word-title {
  font-family: "Fraunces", "Georgia", serif;
  letter-spacing: 0.01em;
}

.stApp {
  background:
    radial-gradient(circle at 20% 10%, rgba(125, 78, 255, 0.35) 0%, rgba(12, 6, 21, 0.3) 45%, transparent 70%),
    radial-gradient(circle at 80% 20%, rgba(255, 120, 200, 0.25) 0%, rgba(11, 6, 21, 0.4) 40%, transparent 70%),
    linear-gradient(160deg, var(--bg-0) 0%, var(--bg-1) 50%, var(--bg-2) 100%);
}

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(15, 8, 28, 0.95) 0%, rgba(18, 9, 35, 0.95) 100%);
  border-right: 1px solid rgba(133, 100, 215, 0.2);
}

div[data-testid="stSidebarNav"] {
  display: none;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
  color: var(--ink);
}

section[data-testid="stSidebar"] .stButton > button {
  width: 100%;
  border-radius: 14px;
  border: 1px solid rgba(158, 116, 255, 0.35);
  background: linear-gradient(140deg, rgba(155, 108, 255, 0.35), rgba(92, 51, 190, 0.45));
  color: var(--ink);
  padding: 0.6rem 0.9rem;
  font-size: 0.95rem;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

section[data-testid="stSidebar"] .stButton > button:hover {
  box-shadow: 0 12px 30px rgba(64, 32, 130, 0.4);
  transform: translateY(-1px);
}

.sidebar-card {
  background: rgba(28, 14, 55, 0.85);
  border-radius: 18px;
  padding: 1.2rem;
  border: 1px solid rgba(171, 120, 255, 0.3);
  box-shadow: 0 14px 30px rgba(16, 6, 31, 0.6);
  margin-bottom: 1.2rem;
}

.sidebar-title {
  font-size: 1.2rem;
  margin: 0 0 0.4rem 0;
}

.sidebar-caption {
  color: var(--muted);
  margin: 0;
}

.stButton > button {
  border-radius: 12px;
  border: 1px solid rgba(168, 125, 255, 0.4);
  background: linear-gradient(135deg, rgba(171, 120, 255, 0.35), rgba(84, 45, 170, 0.6));
  color: var(--ink);
  padding: 0.55rem 1.1rem;
  box-shadow: 0 10px 25px rgba(48, 23, 103, 0.4);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  width: 100%;
}

.stButton > button:hover {
  box-shadow: 0 14px 30px rgba(72, 36, 150, 0.55);
  transform: translateY(-1px);
}

input, textarea, .stSelectbox, .stTextInput, .stTextArea {
  color: var(--ink);
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="select"] > div {
  background-color: rgba(17, 9, 33, 0.9) !important;
  border: 1px solid rgba(166, 126, 255, 0.35) !important;
  color: var(--ink) !important;
  box-shadow: inset 0 0 0 1px rgba(86, 52, 160, 0.2);
}

.hero {
  background: linear-gradient(120deg, rgba(92, 48, 186, 0.35), rgba(28, 14, 55, 0.75));
  border-radius: 26px;
  padding: 2.3rem 2.4rem;
  border: 1px solid rgba(165, 124, 255, 0.3);
  box-shadow: 0 18px 40px rgba(26, 9, 55, 0.55);
  animation: floatIn 0.6s ease;
}

.hero-title {
  font-size: 2.6rem;
  margin-bottom: 0.4rem;
}

.hero-subtitle {
  color: var(--muted);
  font-size: 1.05rem;
}

.hero-tags {
  margin-top: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.pill {
  display: inline-flex;
  padding: 0.25rem 0.8rem;
  border-radius: 999px;
  background: rgba(176, 124, 255, 0.2);
  border: 1px solid rgba(176, 124, 255, 0.4);
  color: var(--ink);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.card {
  background: var(--panel);
  border-radius: 22px;
  padding: 1.5rem;
  box-shadow: 0 16px 35px rgba(20, 8, 40, 0.55);
  border: 1px solid rgba(166, 126, 255, 0.2);
  animation: floatIn 0.6s ease;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: var(--panel-strong);
  border-radius: 18px;
  padding: 1.1rem 1.3rem;
  border: 1px solid rgba(173, 128, 255, 0.28);
  box-shadow: 0 12px 25px rgba(23, 9, 46, 0.5);
}

.stat-label {
  color: var(--muted);
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: 600;
  margin-top: 0.3rem;
}

.word-title {
  font-size: 2.4rem;
  font-weight: 700;
}

.flashcard {
  padding: 1.15rem 1.3rem;
}

.flashcard p,
.flashcard li {
  font-size: 1.05rem;
  line-height: 1.6;
}

.flashcard .section-title {
  margin-top: 0.85rem;
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.7rem;
  border-radius: 999px;
  background: rgba(255, 120, 200, 0.22);
  color: var(--ink);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border: 1px solid rgba(255, 120, 200, 0.4);
}

.muted {
  color: var(--muted);
}

.section-title {
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: var(--muted);
  font-size: 0.75rem;
  margin-top: 1rem;
}

.divider {
  height: 1px;
  background: linear-gradient(90deg, rgba(176, 124, 255, 0.1), rgba(176, 124, 255, 0.6), rgba(176, 124, 255, 0.1));
  margin: 1.6rem 0;
}

.glass {
  background: var(--panel-soft);
  border-radius: 20px;
  padding: 1.5rem;
  border: 1px solid rgba(139, 95, 255, 0.25);
}

div[data-testid="stMetric"] {
  background: var(--panel-strong);
  border-radius: 16px;
  padding: 0.75rem 1.2rem;
  border: 1px solid rgba(166, 126, 255, 0.25);
}

.stDataFrame {
  background: var(--panel-strong);
  border-radius: 16px;
}

div[data-testid="stAlert"] {
  border-radius: 16px;
  border: 1px solid rgba(166, 126, 255, 0.25);
}

@keyframes floatIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
