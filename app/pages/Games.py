from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

path = Path(__file__).resolve()
repo_root = path.parents[2] if path.parent.name == "pages" else path.parents[1]
sys.path.insert(0, str(repo_root))

from app.navigation import render_nav
from app.state import ensure_state
from app.ui import apply_theme
from core.crossword import build_crossword_puzzle


_WORD_RE = re.compile(r"[^A-Za-z]")


def _eligible_count() -> int:
    count = 0
    seen: set[str] = set()
    for entry in st.session_state.entries:
        cleaned = _WORD_RE.sub("", entry.word).upper()
        if not cleaned or len(cleaned) < 2 or len(cleaned) > 20:
            continue
        if cleaned in seen:
            continue
        has_any_clue_text = bool(
            (entry.meaning or "").strip()
            or (entry.example or "").strip()
            or any((item or "").strip() for item in entry.synonyms)
            or any((item or "").strip() for item in entry.mnemonics)
        )
        if not has_any_clue_text:
            continue
        seen.add(cleaned)
        count += 1
    return count


def _ensure_crossword_state() -> None:
    if "crossword_seed" not in st.session_state:
        st.session_state.crossword_seed = random.SystemRandom().randint(10_000, 9_999_999)
    if "crossword_target_words" not in st.session_state:
        st.session_state.crossword_target_words = 10
    if "crossword_puzzle" not in st.session_state:
        st.session_state.crossword_puzzle = None
    if "crossword_signature" not in st.session_state:
        st.session_state.crossword_signature = None


def _generate_puzzle(force: bool = False) -> None:
    signature = (
        st.session_state.crossword_seed,
        st.session_state.crossword_target_words,
        len(st.session_state.entries),
    )
    if not force and st.session_state.crossword_signature == signature and st.session_state.crossword_puzzle:
        return

    with st.spinner("Building crossword from your vocabulary list..."):
        st.session_state.crossword_puzzle = build_crossword_puzzle(
            st.session_state.entries,
            target_words=st.session_state.crossword_target_words,
            seed=st.session_state.crossword_seed,
        )
        st.session_state.crossword_signature = signature


_COMPONENT_TEMPLATE = """
<div id="cw-root" class="cw-root" tabindex="0">
  <div class="cw-header">
    <div>
      <div class="cw-kicker">Crossword Arena</div>
      <div class="cw-sub">Click a cell, type letters, and solve clues from your GRE definitions.</div>
    </div>
    <div class="cw-actions">
      <button id="cw-reveal-all" type="button" class="cw-reveal-btn">Show All Solutions</button>
      <div id="cw-progress" class="cw-progress">0/0 solved</div>
    </div>
  </div>

  <div class="cw-layout">
    <div id="cw-grid" class="cw-grid"></div>
    <div id="cw-clues-wrap" class="cw-clues-wrap">
      <div class="cw-clues cw-clues-across">
        <h4>Across</h4>
        <div id="cw-across" class="cw-clue-list"></div>
      </div>
      <div class="cw-clues cw-clues-down">
        <h4>Down</h4>
        <div id="cw-down" class="cw-clue-list"></div>
      </div>
      <div class="cw-clues cw-clues-solved">
        <h4>Solved</h4>
        <div id="cw-solved" class="cw-clue-list"></div>
      </div>
    </div>
  </div>

  <div class="cw-help">Keyboard: letters to fill, Backspace to erase, Tab to switch direction, arrows to move.</div>
  <div id="cw-solved-overlay" class="cw-solved-overlay"></div>
  <div id="cw-recap" class="cw-recap">
    <div class="cw-recap-title">Puzzle Complete</div>
    <div class="cw-recap-sub">Mini flashcards for every crossword word. Click a card to flip.</div>
    <div id="cw-recap-grid" class="cw-recap-grid"></div>
  </div>
</div>

<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Space+Grotesk:wght@400;500;600&display=swap');

:root {
  --bg: rgba(18, 10, 34, 0.9);
  --panel: rgba(25, 13, 46, 0.88);
  --panel-2: rgba(31, 17, 58, 0.94);
  --ink: #f4efff;
  --muted: #c6b6e4;
  --accent: #b07cff;
  --accent-soft: rgba(176, 124, 255, 0.32);
  --accent-alt: #4de6d6;
  --good: #52e29a;
  --good-soft: rgba(82, 226, 154, 0.25);
  --bad: #ff8ea8;
  --cell-size: 40px;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  font-family: "Space Grotesk", "Segoe UI", sans-serif;
  background: transparent;
  color: var(--ink);
}

.cw-root {
  position: relative;
  background: linear-gradient(140deg, rgba(22, 11, 42, 0.96), rgba(14, 8, 28, 0.95));
  border: 1px solid rgba(171, 120, 255, 0.28);
  border-radius: 20px;
  padding: 1rem;
  box-shadow: inset 0 0 40px rgba(74, 33, 150, 0.22), 0 18px 35px rgba(12, 5, 26, 0.55);
  outline: none;
}

.cw-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.9rem;
}

.cw-kicker {
  font-family: "Fraunces", "Georgia", serif;
  font-size: 1.2rem;
}

.cw-sub {
  color: var(--muted);
  font-size: 0.9rem;
}

.cw-progress {
  border-radius: 999px;
  padding: 0.28rem 0.78rem;
  border: 1px solid rgba(176, 124, 255, 0.5);
  background: rgba(176, 124, 255, 0.18);
  font-size: 0.82rem;
  white-space: nowrap;
}

.cw-actions {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.cw-reveal-btn {
  border-radius: 10px;
  border: 1px solid rgba(176, 124, 255, 0.45);
  background: rgba(176, 124, 255, 0.16);
  color: var(--ink);
  font-size: 0.72rem;
  letter-spacing: 0.02em;
  padding: 0.28rem 0.6rem;
  white-space: nowrap;
  cursor: pointer;
}

.cw-reveal-btn:hover {
  border-color: rgba(176, 124, 255, 0.75);
  background: rgba(176, 124, 255, 0.28);
}

.cw-reveal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cw-layout {
  display: grid;
  grid-template-columns: minmax(280px, auto) minmax(260px, 1fr);
  gap: 1rem;
  align-items: start;
}

.cw-grid {
  display: grid;
  gap: 4px;
  justify-content: start;
  align-content: start;
  background: rgba(10, 5, 22, 0.5);
  border-radius: 14px;
  padding: 0.55rem;
  border: 1px solid rgba(158, 116, 255, 0.25);
}

.cw-cell {
  width: var(--cell-size);
  height: var(--cell-size);
  border-radius: 9px;
  border: 1px solid rgba(158, 116, 255, 0.25);
  background: linear-gradient(165deg, rgba(28, 14, 55, 0.96), rgba(17, 8, 32, 0.95));
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  user-select: none;
  transition: transform 0.12s ease, border-color 0.12s ease, box-shadow 0.12s ease;
}

.cw-cell:hover {
  transform: translateY(-1px);
  border-color: rgba(176, 124, 255, 0.45);
}

.cw-cell.block {
  background: rgba(8, 4, 16, 0.4);
  border-color: rgba(84, 49, 148, 0.25);
  cursor: default;
}

.cw-cell.active-word {
  box-shadow: inset 0 0 0 1px rgba(176, 124, 255, 0.68);
}

.cw-cell.selected {
  border-color: var(--accent-alt);
  box-shadow: 0 0 0 2px rgba(77, 230, 214, 0.25), inset 0 0 0 1px rgba(77, 230, 214, 0.85);
}

.cw-cell.solved {
  border-color: var(--good);
  background: linear-gradient(165deg, rgba(21, 55, 43, 0.88), rgba(12, 30, 25, 0.88));
  box-shadow: inset 0 0 0 1px rgba(82, 226, 154, 0.7), 0 0 0 1px rgba(82, 226, 154, 0.25);
}

.cw-letter {
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.cw-cell.typed-wrong .cw-letter {
  color: var(--bad);
}

.cw-cell.typed-right .cw-letter {
  color: #ddfbe9;
}

.cw-cell.clue-filled:not(.solved) .cw-letter,
.cw-cell.clue-filled:not(.solved).typed-right .cw-letter {
  color: #ffe066;
  text-shadow: 0 0 8px rgba(255, 224, 102, 0.45);
}

.cw-number {
  position: absolute;
  top: 2px;
  left: 4px;
  font-size: 0.56rem;
  color: #c6b6e4;
}

.cw-clues-wrap {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.cw-clues {
  background: var(--panel);
  border: 1px solid rgba(169, 126, 255, 0.24);
  border-radius: 12px;
  padding: 0.7rem;
  display: flex;
  flex-direction: column;
}

.cw-clue-list {
  max-height: none;
  overflow: visible;
  padding-right: 0.15rem;
}

.cw-clue-list::-webkit-scrollbar {
  width: 7px;
}

.cw-clue-list::-webkit-scrollbar-thumb {
  background: rgba(155, 122, 226, 0.46);
  border-radius: 999px;
}

.cw-clues-solved {
  border-color: rgba(96, 212, 150, 0.35);
  background: linear-gradient(140deg, rgba(20, 58, 44, 0.74), rgba(14, 35, 29, 0.72));
}

.cw-clues-wrap.scroll-active {
  height: var(--clue-pane-height, 540px);
}

.cw-clues-wrap.scroll-active .cw-clues-across,
.cw-clues-wrap.scroll-active .cw-clues-down {
  flex: 1 1 0;
  min-height: 0;
}

.cw-clues-wrap.scroll-active .cw-clues-solved {
  flex: 0.85 1 0;
  min-height: 0;
}

.cw-clues-wrap.scroll-active .cw-clue-list {
  overflow-y: auto;
  min-height: 0;
}

.cw-clues h4 {
  margin: 0 0 0.45rem 0;
  font-family: "Fraunces", "Georgia", serif;
  font-size: 1.04rem;
}

.cw-clue {
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 0.45rem 0.5rem;
  margin-bottom: 0.35rem;
  background: var(--panel-2);
  color: var(--ink);
  display: block;
  font-size: 0.84rem;
  cursor: pointer;
}

.cw-clue:hover {
  border-color: rgba(176, 124, 255, 0.45);
}

.cw-clue.active {
  border-color: var(--accent-alt);
  box-shadow: inset 0 0 0 1px rgba(77, 230, 214, 0.35);
}

.cw-clue.solved {
  border-color: rgba(82, 226, 154, 0.75);
  background: linear-gradient(120deg, rgba(26, 66, 51, 0.85), rgba(18, 42, 34, 0.86));
}

.cw-clue.solved-item {
  opacity: 0.92;
}

.cw-clue.solved-item.newly-solved {
  animation: solvedFadeIn 0.45s ease;
}

.cw-solved-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.38rem;
  align-content: flex-start;
}

.cw-solved-chip {
  position: relative;
  border: 1px solid rgba(117, 230, 168, 0.52);
  background: rgba(44, 116, 83, 0.35);
  color: #e9fff2;
  border-radius: 999px;
  padding: 0.22rem 0.55rem;
  font-size: 0.73rem;
  line-height: 1.2;
  cursor: pointer;
}

.cw-solved-chip:hover,
.cw-solved-chip:focus-visible {
  border-color: rgba(117, 230, 168, 0.85);
  background: rgba(44, 116, 83, 0.5);
  outline: none;
}

.cw-solved-empty {
  color: var(--muted);
  font-size: 0.78rem;
  padding: 0.2rem 0.05rem;
}

.cw-solved-overlay {
  position: absolute;
  left: 0.8rem;
  right: 0.8rem;
  bottom: 0.8rem;
  background: rgba(10, 24, 18, 0.98);
  border: 1px solid rgba(117, 230, 168, 0.55);
  border-radius: 10px;
  color: #e9fff2;
  font-size: 0.78rem;
  line-height: 1.3;
  padding: 0.45rem 0.55rem;
  box-shadow: 0 14px 30px rgba(5, 13, 10, 0.58);
  opacity: 0;
  pointer-events: none;
  transform: translateY(5px);
  transition: opacity 0.15s ease, transform 0.15s ease;
  z-index: 40;
}

.cw-solved-overlay.show {
  opacity: 1;
  transform: translateY(0);
}

.cw-clue-num {
  color: #d6c5f0;
  font-weight: 600;
  min-width: 18px;
  margin-right: 0.42rem;
}

.cw-clue-len {
  color: var(--muted);
}

.cw-clue-head {
  display: flex;
  align-items: flex-start;
}

.cw-clue-main {
  flex: 1;
}

.cw-hint-meta {
  margin-top: 0.4rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.cw-hint-track {
  position: relative;
  height: 7px;
  border-radius: 999px;
  flex: 1;
  overflow: hidden;
  background: rgba(20, 64, 42, 0.36);
  border: 1px solid rgba(95, 201, 138, 0.42);
  box-shadow: inset 0 0 10px rgba(14, 42, 28, 0.5);
}

.cw-hint-fill {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #9dffbf, #3fd980);
  box-shadow: 0 0 12px rgba(72, 235, 144, 0.45);
}

.cw-hint-left {
  color: var(--muted);
  font-size: 0.69rem;
  white-space: nowrap;
}

.cw-hint-btn {
  border-radius: 8px;
  border: 1px solid rgba(176, 124, 255, 0.4);
  background: rgba(176, 124, 255, 0.18);
  color: var(--ink);
  padding: 0.2rem 0.46rem;
  font-size: 0.68rem;
  white-space: nowrap;
  cursor: pointer;
}

.cw-hint-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.cw-help {
  margin-top: 0.75rem;
  color: var(--muted);
  font-size: 0.83rem;
  border-top: 1px solid rgba(166, 126, 255, 0.2);
  padding-top: 0.6rem;
}

.cw-recap {
  margin-top: 0.95rem;
  border-top: 1px solid rgba(166, 126, 255, 0.24);
  padding-top: 0.8rem;
  display: none;
}

.cw-recap.show {
  display: block;
}

.cw-recap-title {
  font-family: "Fraunces", "Georgia", serif;
  font-size: 1.05rem;
}

.cw-recap-sub {
  margin-top: 0.2rem;
  color: var(--muted);
  font-size: 0.82rem;
}

.cw-recap-grid {
  margin-top: 0.6rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.55rem;
}

.cw-mini-card {
  position: relative;
  min-height: 92px;
  border-radius: 12px;
  border: 1px solid rgba(156, 112, 242, 0.36);
  background: linear-gradient(150deg, rgba(28, 14, 54, 0.95), rgba(18, 9, 35, 0.95));
  color: var(--ink);
  cursor: pointer;
  text-align: left;
  padding: 0.6rem 0.65rem;
}

.cw-mini-card:hover {
  border-color: rgba(176, 124, 255, 0.7);
}

.cw-mini-front {
  display: block;
}

.cw-mini-word {
  display: block;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.cw-mini-meta {
  display: block;
  margin-top: 0.2rem;
  font-size: 0.72rem;
  color: var(--muted);
}

.cw-mini-back {
  display: none;
  font-size: 0.79rem;
  color: #e9deff;
  line-height: 1.4;
}

.cw-mini-card.flipped .cw-mini-front {
  display: none;
}

.cw-mini-card.flipped .cw-mini-back {
  display: block;
}

@media (max-width: 920px) {
  .cw-layout {
    grid-template-columns: 1fr;
  }

  .cw-grid {
    justify-content: center;
  }

  .cw-cell {
    width: calc(var(--cell-size) - 2px);
    height: calc(var(--cell-size) - 2px);
  }

  .cw-clue-list {
    max-height: 160px;
  }
}

@keyframes solvedFadeIn {
  from {
    opacity: 0.2;
    transform: translateY(4px);
  }
  to {
    opacity: 0.92;
    transform: translateY(0);
  }
}
</style>

<script>
(function () {
  const puzzle = __PUZZLE_JSON__;
  if (!puzzle || !Array.isArray(puzzle.grid) || !Array.isArray(puzzle.words)) {
    return;
  }

  const root = document.getElementById("cw-root");
  const gridEl = document.getElementById("cw-grid");
  const cluesWrapEl = document.getElementById("cw-clues-wrap");
  const acrossEl = document.getElementById("cw-across");
  const downEl = document.getElementById("cw-down");
  const solvedEl = document.getElementById("cw-solved");
  const solvedOverlayEl = document.getElementById("cw-solved-overlay");
  const revealAllBtn = document.getElementById("cw-reveal-all");
  const progressEl = document.getElementById("cw-progress");
  const recapEl = document.getElementById("cw-recap");
  const recapGridEl = document.getElementById("cw-recap-grid");

  const cellSize = puzzle.cols > 14 ? 32 : (puzzle.cols > 11 ? 36 : 40);
  root.style.setProperty("--cell-size", `${cellSize}px`);
  gridEl.style.gridTemplateColumns = `repeat(${puzzle.cols}, var(--cell-size))`;

  const wordsById = {};
  const cellMembership = {};
  const startNumbers = {};
  const startWordMembership = {};

  for (const word of puzzle.words) {
    wordsById[word.id] = word;
    const startKey = `${word.row}-${word.col}`;
    startNumbers[startKey] = word.number;
    if (!startWordMembership[startKey]) {
      startWordMembership[startKey] = [];
    }
    startWordMembership[startKey].push(word.id);
    for (const cell of word.cells) {
      const key = `${cell[0]}-${cell[1]}`;
      if (!cellMembership[key]) {
        cellMembership[key] = { across: null, down: null, words: [] };
      }
      cellMembership[key].words.push(word.id);
      if (word.direction === "across") {
        cellMembership[key].across = word.id;
      } else {
        cellMembership[key].down = word.id;
      }
    }
  }

  const state = {
    selected: puzzle.words.length ? `${puzzle.words[0].row}-${puzzle.words[0].col}` : null,
    direction: "across",
    letters: {},
    locked: new Set(),
    hintUsage: {},
    clueCells: new Set(),
    clueLocked: new Set(),
    seenSolvedWords: new Set(),
    pendingScrollWordId: null,
  };

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function getWordFromSelection() {
    if (!state.selected) {
      return null;
    }
    const meta = cellMembership[state.selected];
    if (!meta) {
      return null;
    }
    const preferred = meta[state.direction];
    if (preferred) {
      return wordsById[preferred] || null;
    }
    const fallback = meta.across || meta.down;
    if (!fallback) {
      return null;
    }
    state.direction = meta.across ? "across" : "down";
    return wordsById[fallback] || null;
  }

  function startWordIdForCell(key) {
    const startWords = startWordMembership[key] || [];
    if (!startWords.length) {
      return null;
    }
    for (const wordId of startWords) {
      const word = wordsById[wordId];
      if (word && word.direction === state.direction) {
        return wordId;
      }
    }
    return startWords[0] || null;
  }

  function isWordSolved(word) {
    for (const [row, col] of word.cells) {
      const key = keyForCell(row, col);
      const expected = puzzle.grid[row][col];
      if ((state.letters[key] || "") !== expected) {
        return false;
      }
    }
    return true;
  }

  function keyForCell(row, col) {
    return `${row}-${col}`;
  }

  function parseKey(key) {
    const [row, col] = key.split("-").map(Number);
    return { row, col };
  }

  function findNextPlayable(key, dr, dc) {
    const start = parseKey(key);
    let row = start.row + dr;
    let col = start.col + dc;
    while (row >= 0 && col >= 0 && row < puzzle.rows && col < puzzle.cols) {
      if (puzzle.grid[row][col]) {
        return keyForCell(row, col);
      }
      row += dr;
      col += dc;
    }
    return null;
  }

  function isLocked(key) {
    return state.locked.has(key) || state.clueLocked.has(key);
  }

  function moveSelectionInWord(word, step, requireEditable = false) {
    if (!word || !state.selected) {
      return false;
    }
    const currentIdx = word.cells.findIndex((cell) => keyForCell(cell[0], cell[1]) === state.selected);
    if (currentIdx < 0) {
      return false;
    }

    for (
      let idx = currentIdx + step;
      idx >= 0 && idx < word.cells.length;
      idx += step
    ) {
      const [row, col] = word.cells[idx];
      const key = keyForCell(row, col);
      if (requireEditable && isLocked(key)) {
        continue;
      }
      state.selected = key;
      return true;
    }

    return false;
  }

  function solvedWordIds() {
    const solved = new Set();
    for (const word of puzzle.words) {
      let ok = true;
      for (let idx = 0; idx < word.cells.length; idx += 1) {
        const [row, col] = word.cells[idx];
        const key = keyForCell(row, col);
        const expected = puzzle.grid[row][col];
        if ((state.letters[key] || "") !== expected) {
          ok = false;
          break;
        }
      }
      if (ok) {
        solved.add(word.id);
      }
    }
    return solved;
  }

  function selectWord(wordId) {
    const word = wordsById[wordId];
    if (!word) {
      return;
    }
    state.direction = word.direction;
    state.selected = keyForCell(word.row, word.col);
    root.focus();
    render();
  }

  function hintsUsed(word) {
    const used = Number(state.hintUsage[word.id] || 0);
    const maxAllowed = 2;
    return Math.max(0, Math.min(used, maxAllowed));
  }

  function cluesLeft(word) {
    return Math.max(0, 2 - hintsUsed(word));
  }

  function wordCellInfo(word, idx) {
    const [row, col] = word.cells[idx];
    const key = keyForCell(row, col);
    const expected = puzzle.grid[row][col];
    const current = state.letters[key] || "";
    const fixed = isLocked(key) || current === expected;
    return { row, col, key, expected, fixed };
  }

  function randomFrom(items) {
    if (!items || items.length === 0) {
      return null;
    }
    const idx = Math.floor(Math.random() * items.length);
    return items[idx];
  }

  function pickRandomMiddleIndex(word, blocked = new Set()) {
    const middle = [];
    for (let idx = 1; idx < word.length - 1; idx += 1) {
      if (blocked.has(idx)) {
        continue;
      }
      const info = wordCellInfo(word, idx);
      if (!info.fixed) {
        middle.push(idx);
      }
    }
    return randomFrom(middle);
  }

  function pickRandomAnyUnfixedIndex(word, blocked = new Set()) {
    const anyUnfixed = [];
    for (let idx = 0; idx < word.length; idx += 1) {
      if (blocked.has(idx)) {
        continue;
      }
      const info = wordCellInfo(word, idx);
      if (!info.fixed) {
        anyUnfixed.push(idx);
      }
    }
    return randomFrom(anyUnfixed);
  }

  function targetIndexForClue(word, usedCount) {
    const firstIdx = 0;
    const lastIdx = word.length - 1;
    const firstFixed = wordCellInfo(word, firstIdx).fixed;
    const lastFixed = wordCellInfo(word, lastIdx).fixed;

    if (usedCount === 0) {
      if (!firstFixed) {
        return firstIdx;
      }
      if (!lastFixed) {
        return lastIdx;
      }
      return pickRandomMiddleIndex(word) ?? pickRandomAnyUnfixedIndex(word);
    }

    if (!lastFixed) {
      return lastIdx;
    }

    return pickRandomMiddleIndex(word) ?? pickRandomAnyUnfixedIndex(word, new Set([firstIdx, lastIdx]));
  }

  function revealLetterForClue(word, usedCount) {
    const idx = targetIndexForClue(word, usedCount);
    if (idx === null || idx === undefined) {
      return 0;
    }
    const info = wordCellInfo(word, idx);
    if (info.fixed) {
      return 0;
    }
    state.letters[info.key] = info.expected;
    state.clueCells.add(info.key);
    state.clueLocked.add(info.key);
    return 1;
  }

  function revealHint(wordId) {
    const word = wordsById[wordId];
    if (!word) {
      return;
    }
    const used = hintsUsed(word);
    const maxAllowed = 2;
    if (used >= maxAllowed) {
      return;
    }
    const revealCount = revealLetterForClue(word, used);
    if (revealCount === 0) {
      return;
    }
    state.hintUsage[wordId] = used + 1;
    render();
  }

  function revealAllSolutions() {
    for (let row = 0; row < puzzle.rows; row += 1) {
      for (let col = 0; col < puzzle.cols; col += 1) {
        const expected = puzzle.grid[row][col];
        if (!expected) {
          continue;
        }
        const key = keyForCell(row, col);
        state.letters[key] = expected;
        state.locked.add(key);
        state.clueLocked.add(key);
      }
    }
    render();
  }

  function scrollToWordClue(wordId) {
    if (!wordId) {
      return;
    }
    const target = root.querySelector(
      `.cw-clue[data-word-id="${wordId}"], .cw-solved-chip[data-word-id="${wordId}"]`
    );
    if (!target) {
      return;
    }
    target.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
  }

  function showSolvedOverlay(text) {
    if (!solvedOverlayEl) {
      return;
    }
    if (!text) {
      solvedOverlayEl.textContent = "";
      solvedOverlayEl.classList.remove("show");
      return;
    }
    solvedOverlayEl.textContent = text;
    solvedOverlayEl.classList.add("show");
  }

  function syncPaneOverflow() {
    if (!cluesWrapEl || !gridEl) {
      return;
    }
    cluesWrapEl.classList.remove("scroll-active");
    cluesWrapEl.style.removeProperty("--clue-pane-height");

    const gridHeight = Math.ceil(gridEl.getBoundingClientRect().height);
    const contentHeight = Math.ceil(cluesWrapEl.scrollHeight);
    if (contentHeight > gridHeight + 4) {
      cluesWrapEl.classList.add("scroll-active");
      cluesWrapEl.style.setProperty("--clue-pane-height", `${gridHeight}px`);
    }
  }

  function renderRecap(solved) {
    const isComplete = puzzle.words.length > 0 && solved.size === puzzle.words.length;
    if (!isComplete) {
      recapEl.classList.remove("show");
      recapGridEl.innerHTML = "";
      return;
    }

    recapEl.classList.add("show");
    recapGridEl.innerHTML = "";
    const orderedWords = [...puzzle.words].sort((a, b) => a.number - b.number || a.direction.localeCompare(b.direction));

    for (const word of orderedWords) {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "cw-mini-card";
      card.innerHTML = `
        <span class="cw-mini-front">
          <span class="cw-mini-word">${escapeHtml(word.answer)}</span>
          <span class="cw-mini-meta">${escapeHtml(word.direction)} ${word.number}</span>
        </span>
        <span class="cw-mini-back">${escapeHtml(word.clue)}</span>
      `;
      card.addEventListener("click", () => {
        card.classList.toggle("flipped");
      });
      recapGridEl.appendChild(card);
    }
  }

  function render() {
    const currentWord = getWordFromSelection();
    const currentWordCells = new Set(
      currentWord ? currentWord.cells.map((cell) => keyForCell(cell[0], cell[1])) : []
    );

    const solved = solvedWordIds();
    const solvedCells = new Set();
    for (const wordId of solved) {
      const word = wordsById[wordId];
      for (const cell of word.cells) {
        const key = keyForCell(cell[0], cell[1]);
        solvedCells.add(key);
        state.locked.add(key);
      }
    }

    progressEl.textContent = `${solved.size}/${puzzle.words.length} solved`;
    if (revealAllBtn) {
      const isComplete = solved.size === puzzle.words.length;
      revealAllBtn.disabled = isComplete;
      revealAllBtn.textContent = isComplete ? "Solutions Shown" : "Show All Solutions";
    }
    renderRecap(solved);

    gridEl.innerHTML = "";
    for (let row = 0; row < puzzle.rows; row += 1) {
      for (let col = 0; col < puzzle.cols; col += 1) {
        const solution = puzzle.grid[row][col];
        const key = keyForCell(row, col);
        const cell = document.createElement("div");

        if (!solution) {
          cell.className = "cw-cell block";
          gridEl.appendChild(cell);
          continue;
        }

        let className = "cw-cell";
        if (state.selected === key) className += " selected";
        if (currentWordCells.has(key)) className += " active-word";
        if (solvedCells.has(key)) className += " solved";
        if (isLocked(key)) className += " locked";
        if (state.clueCells.has(key)) className += " clue-filled";

        const typed = state.letters[key] || "";
        if (typed) {
          if (typed === solution) {
            className += " typed-right";
          } else {
            className += " typed-wrong";
          }
        }

        cell.className = className;
        cell.setAttribute("data-key", key);

        const number = startNumbers[key];
        if (number) {
          const numEl = document.createElement("span");
          numEl.className = "cw-number";
          numEl.textContent = String(number);
          cell.appendChild(numEl);
        }

        const letterEl = document.createElement("span");
        letterEl.className = "cw-letter";
        letterEl.textContent = typed;
        cell.appendChild(letterEl);

        cell.addEventListener("click", () => {
          if (state.selected === key) {
            const meta = cellMembership[key];
            if (meta && meta.across && meta.down) {
              state.direction = state.direction === "across" ? "down" : "across";
            }
          } else {
            state.selected = key;
            const meta = cellMembership[key];
            if (meta && !meta[state.direction]) {
              state.direction = meta.across ? "across" : "down";
            }
          }
          state.pendingScrollWordId = startWordIdForCell(key);
          root.focus();
          render();
        });

        gridEl.appendChild(cell);
      }
    }

    function renderClueBucket(container, words) {
      container.innerHTML = "";
      for (const word of words) {
        if (solved.has(word.id)) {
          continue;
        }
        const clue = document.createElement("div");
        let clueClass = "cw-clue";
        if (currentWord && currentWord.id === word.id) clueClass += " active";
        clue.className = clueClass;
        clue.setAttribute("data-word-id", word.id);
        clue.setAttribute("role", "button");
        clue.setAttribute("tabindex", "0");

        const head = document.createElement("div");
        head.className = "cw-clue-head";

        const num = document.createElement("span");
        num.className = "cw-clue-num";
        num.textContent = String(word.number);

        const text = document.createElement("span");
        text.className = "cw-clue-main";
        text.innerHTML = `${escapeHtml(word.clue)} <span class=\"cw-clue-len\">(${word.length})</span>`;

        head.appendChild(num);
        head.appendChild(text);
        clue.appendChild(head);

        const left = cluesLeft(word);

        const meta = document.createElement("div");
        meta.className = "cw-hint-meta";
        const healthPct = Math.max(0, Math.min(100, (left / 2) * 100));
        meta.innerHTML = `
          <button type="button" class="cw-hint-btn" ${left === 0 ? "disabled" : ""}>${left > 0 ? "Use Clue" : "No Clues"}</button>
          <span class="cw-hint-track"><span class="cw-hint-fill" style="width:${healthPct}%"></span></span>
          <span class="cw-hint-left">${left} clue${left === 1 ? "" : "s"} left</span>
        `;
        clue.appendChild(meta);

        const hintButton = meta.querySelector(".cw-hint-btn");
        if (!hintButton) {
          continue;
        }
        hintButton.addEventListener("click", (event) => {
          event.stopPropagation();
          revealHint(word.id);
        });

        clue.addEventListener("click", () => selectWord(word.id));
        clue.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            selectWord(word.id);
          }
        });
        container.appendChild(clue);
      }
    }

    function renderSolvedBucket(container, words) {
      container.innerHTML = "";
      const solvedWords = words.filter((word) => solved.has(word.id));
      solvedWords.sort((a, b) => a.number - b.number || a.direction.localeCompare(b.direction));

      if (!solvedWords.length) {
        const empty = document.createElement("div");
        empty.className = "cw-solved-empty";
        empty.textContent = "Solved words will appear here.";
        container.appendChild(empty);
        showSolvedOverlay("");
        return;
      }

      const chips = document.createElement("div");
      chips.className = "cw-solved-grid";
      for (const word of solvedWords) {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "cw-solved-chip";
        chip.setAttribute("data-word-id", word.id);
        chip.textContent = word.answer;
        chip.addEventListener("click", () => selectWord(word.id));
        chip.addEventListener("mouseenter", () => showSolvedOverlay(word.clue));
        chip.addEventListener("focus", () => showSolvedOverlay(word.clue));
        chip.addEventListener("mouseleave", () => showSolvedOverlay(""));
        chip.addEventListener("blur", () => showSolvedOverlay(""));
        chips.appendChild(chip);
        state.seenSolvedWords.add(word.id);
      }
      container.appendChild(chips);
    }

    renderClueBucket(acrossEl, puzzle.across);
    renderClueBucket(downEl, puzzle.down);
    renderSolvedBucket(solvedEl, puzzle.words);
    syncPaneOverflow();
    if (state.pendingScrollWordId) {
      scrollToWordClue(state.pendingScrollWordId);
      state.pendingScrollWordId = null;
    }
  }

  function moveSelectionInDirection(step) {
    if (!state.selected) {
      return;
    }
    const dr = state.direction === "across" ? 0 : 1;
    const dc = state.direction === "across" ? 1 : 0;
    const next = findNextPlayable(state.selected, dr * step, dc * step);
    if (next) {
      state.selected = next;
    }
  }

  function handleKeyDown(event) {
    const targetTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
    if (targetTag === "input" || targetTag === "textarea") {
      return;
    }
    if (!state.selected) {
      return;
    }

    if (/^[a-zA-Z]$/.test(event.key)) {
      const selectedWord = getWordFromSelection();
      if (!selectedWord) {
        event.preventDefault();
        return;
      }
      if (isWordSolved(selectedWord)) {
        event.preventDefault();
        return;
      }
      if (isLocked(state.selected)) {
        if (!moveSelectionInWord(selectedWord, 1, true)) {
          render();
          event.preventDefault();
          return;
        }
      }
      if (!state.selected || isLocked(state.selected)) {
        render();
        event.preventDefault();
        return;
      }
      state.letters[state.selected] = event.key.toUpperCase();
      moveSelectionInWord(selectedWord, 1, true);
      render();
      event.preventDefault();
      return;
    }

    if (event.key === "Backspace" || event.key === "Delete") {
      const selectedWord = getWordFromSelection();
      if (!selectedWord) {
        event.preventDefault();
        return;
      }
      if (isWordSolved(selectedWord)) {
        event.preventDefault();
        return;
      }
      if (isLocked(state.selected)) {
        moveSelectionInWord(selectedWord, -1, true);
        render();
        event.preventDefault();
        return;
      }
      if (state.letters[state.selected]) {
        delete state.letters[state.selected];
      } else {
        moveSelectionInWord(selectedWord, -1, true);
        if (state.selected && !isLocked(state.selected)) {
          delete state.letters[state.selected];
        }
      }
      render();
      event.preventDefault();
      return;
    }

    if (event.key === "Tab") {
      state.direction = state.direction === "across" ? "down" : "across";
      render();
      event.preventDefault();
      return;
    }

    if (event.key === "ArrowUp") {
      const next = findNextPlayable(state.selected, -1, 0);
      if (next) {
        state.selected = next;
        state.direction = "down";
        render();
      }
      event.preventDefault();
      return;
    }

    if (event.key === "ArrowDown") {
      const next = findNextPlayable(state.selected, 1, 0);
      if (next) {
        state.selected = next;
        state.direction = "down";
        render();
      }
      event.preventDefault();
      return;
    }

    if (event.key === "ArrowLeft") {
      const next = findNextPlayable(state.selected, 0, -1);
      if (next) {
        state.selected = next;
        state.direction = "across";
        render();
      }
      event.preventDefault();
      return;
    }

    if (event.key === "ArrowRight") {
      const next = findNextPlayable(state.selected, 0, 1);
      if (next) {
        state.selected = next;
        state.direction = "across";
        render();
      }
      event.preventDefault();
    }
  }

  document.addEventListener("keydown", handleKeyDown);
  if (revealAllBtn) {
    revealAllBtn.addEventListener("click", () => {
      revealAllSolutions();
      root.focus();
    });
  }
  window.addEventListener("resize", () => {
    syncPaneOverflow();
  });
  root.focus();
  render();
})();
</script>
"""


def _render_crossword(puzzle: dict[str, object]) -> None:
    html = _COMPONENT_TEMPLATE.replace("__PUZZLE_JSON__", json.dumps(puzzle))
    rows = int(puzzle.get("rows", 12))
    cols = int(puzzle.get("cols", 12))
    base_height = 570 + rows * 36
    if cols > 12:
        base_height += 50
    height = max(760, min(base_height, 1400))
    components.html(html, height=height)


st.set_page_config(page_title="Games", layout="wide")
apply_theme()
render_nav()
ensure_state()
_ensure_crossword_state()

st.markdown(
    """
    <div class="hero">
      <div class="hero-title">Games</div>
      <div class="hero-subtitle">Train recall in a sleek crossword built from your GRE master list.</div>
      <div class="hero-tags">
        <span class="pill">Crossword</span>
        <span class="pill">Definitions as clues</span>
        <span class="pill">Keyboard-first</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.entries:
    st.info("No entries loaded yet. Rebuild the dataset on Home.")
    st.stop()

eligible_words = _eligible_count()

st.markdown("<div class='card'>", unsafe_allow_html=True)
col_a, col_b, col_c = st.columns([1.4, 1, 1])
with col_a:
    st.slider(
        "Words in puzzle",
        min_value=6,
        max_value=16,
        step=1,
        key="crossword_target_words",
        help="Higher values create denser, harder grids.",
    )
with col_b:
    st.metric("Crossword pool", f"{eligible_words:,}")
with col_c:
    st.caption("")
    st.caption("")
    if st.button("Generate New Crossword", use_container_width=True):
        st.session_state.crossword_seed += 1
        _generate_puzzle(force=True)

st.markdown(
    "<div class='flash-note'>Select a square and type directly. Solved words glow green across their letter blocks.</div>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

_generate_puzzle(force=False)

puzzle = st.session_state.crossword_puzzle
if not puzzle:
    st.warning(
        "Could not generate a crossword with current constraints. Try again or reduce words in puzzle."
    )
    st.stop()

_render_crossword(puzzle)
