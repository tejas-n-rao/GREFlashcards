from __future__ import annotations

from dataclasses import dataclass
import random
import re
from typing import Sequence

from core.models import WordEntry


_WORD_RE = re.compile(r"[^A-Za-z]")
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class _Candidate:
    answer: str
    clue: str
    hints: list[str]


@dataclass
class _Placement:
    answer: str
    clue: str
    hints: list[str]
    row: int
    col: int
    direction: str  # across | down


@dataclass
class _Cell:
    letter: str
    across: bool = False
    down: bool = False


@dataclass(frozen=True)
class _Probe:
    row: int
    col: int
    direction: str


def _clean_word(word: str) -> str:
    return _WORD_RE.sub("", word).upper()


def _clean_clue(clue: str | None) -> str:
    if not clue:
        return ""
    normalized = _WHITESPACE_RE.sub(" ", clue).strip()
    if len(normalized) <= 160:
        return normalized
    trimmed = normalized[:157].rstrip(" ,;:-")
    return f"{trimmed}..."


def _derive_primary_clue(entry: WordEntry) -> str:
    """Prefer definition, then fall back to other study metadata."""
    direct = _clean_clue(entry.meaning)
    if direct:
        return direct

    example = _clean_clue(entry.example)
    if example:
        return f"From example: {example}"

    if entry.synonyms:
        synonym = _clean_clue(entry.synonyms[0])
        if synonym:
            return f"Synonym cue: {synonym}"

    if entry.mnemonics:
        mnemonic = _clean_clue(entry.mnemonics[0])
        if mnemonic:
            return f"Mnemonic cue: {mnemonic}"

    return ""


def _clean_hint(text: str | None, *, max_len: int = 88) -> str:
    if not text:
        return ""
    normalized = _WHITESPACE_RE.sub(" ", text).strip()
    if len(normalized) <= max_len:
        return normalized
    trimmed = normalized[: max_len - 3].rstrip(" ,;:-")
    return f"{trimmed}..."


def _build_hints(entry: WordEntry, answer: str) -> list[str]:
    raw_hints: list[str] = []

    if entry.pos:
        hint = _clean_hint(entry.pos, max_len=40)
        if hint:
            raw_hints.append(f"Part of speech: {hint}")

    for synonym in entry.synonyms[:4]:
        cleaned = _clean_hint(synonym, max_len=42)
        if not cleaned:
            continue
        if cleaned.upper() == answer:
            continue
        if answer.lower() in cleaned.lower():
            continue
        raw_hints.append(f"Synonym clue: {cleaned}")

    if entry.example:
        example_hint = _clean_hint(entry.example, max_len=80)
        if example_hint and answer.lower() not in example_hint.lower():
            raw_hints.append(f"Context: {example_hint}")

    if entry.mnemonics:
        mnemonic_hint = _clean_hint(entry.mnemonics[0], max_len=70)
        if mnemonic_hint:
            raw_hints.append(f"Memory hook: {mnemonic_hint}")

    # Always provide useful structural backups so each word has 2 hints.
    raw_hints.append(f"Starts with: {answer[0]}")
    raw_hints.append(f"Ends with: {answer[-1]}")

    deduped: list[str] = []
    seen: set[str] = set()
    for hint in raw_hints:
        key = hint.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(hint)
        if len(deduped) == 2:
            break

    return deduped


def _build_candidates(
    entries: Sequence[WordEntry],
    min_word_length: int,
    max_word_length: int,
) -> list[_Candidate]:
    seen: set[str] = set()
    candidates: list[_Candidate] = []
    for entry in entries:
        answer = _clean_word(entry.word)
        if not answer:
            continue
        if not (min_word_length <= len(answer) <= max_word_length):
            continue
        if answer in seen:
            continue
        clue = _derive_primary_clue(entry)
        if not clue:
            continue
        seen.add(answer)
        candidates.append(_Candidate(answer=answer, clue=clue, hints=_build_hints(entry, answer)))
    return candidates


def _can_place(
    grid: dict[tuple[int, int], _Cell],
    word: str,
    row: int,
    col: int,
    direction: str,
) -> tuple[bool, int, int]:
    intersections = 0
    new_cells = 0

    if direction == "across":
        if (row, col - 1) in grid or (row, col + len(word)) in grid:
            return False, 0, 0

        for offset, letter in enumerate(word):
            r = row
            c = col + offset
            existing = grid.get((r, c))
            if existing:
                if existing.letter != letter:
                    return False, 0, 0
                if existing.across:
                    return False, 0, 0
                intersections += 1
                continue

            if (r - 1, c) in grid or (r + 1, c) in grid:
                return False, 0, 0
            new_cells += 1
    else:
        if (row - 1, col) in grid or (row + len(word), col) in grid:
            return False, 0, 0

        for offset, letter in enumerate(word):
            r = row + offset
            c = col
            existing = grid.get((r, c))
            if existing:
                if existing.letter != letter:
                    return False, 0, 0
                if existing.down:
                    return False, 0, 0
                intersections += 1
                continue

            if (r, c - 1) in grid or (r, c + 1) in grid:
                return False, 0, 0
            new_cells += 1

    if grid and intersections == 0:
        return False, 0, 0
    if new_cells == 0:
        return False, 0, 0

    return True, intersections, new_cells


def _apply_placement(
    grid: dict[tuple[int, int], _Cell],
    placement: _Placement,
) -> None:
    is_across = placement.direction == "across"
    for index, letter in enumerate(placement.answer):
        row = placement.row + (0 if is_across else index)
        col = placement.col + (index if is_across else 0)
        existing = grid.get((row, col))
        if existing:
            if is_across:
                existing.across = True
            else:
                existing.down = True
            continue

        grid[(row, col)] = _Cell(letter=letter, across=is_across, down=not is_across)


def _index_letters(grid: dict[tuple[int, int], _Cell]) -> dict[str, list[tuple[int, int]]]:
    index: dict[str, list[tuple[int, int]]] = {}
    for point, cell in grid.items():
        index.setdefault(cell.letter, []).append(point)
    return index


def _random_probe(
    candidate: _Candidate,
    grid: dict[tuple[int, int], _Cell],
    rng: random.Random,
) -> _Probe | None:
    letter_index = _index_letters(grid)
    options: list[_Probe] = []

    for offset, letter in enumerate(candidate.answer):
        for cross_row, cross_col in letter_index.get(letter, []):
            for direction in ("across", "down"):
                row = cross_row if direction == "across" else cross_row - offset
                col = cross_col - offset if direction == "across" else cross_col
                can_place, _, _ = _can_place(
                    grid=grid,
                    word=candidate.answer,
                    row=row,
                    col=col,
                    direction=direction,
                )
                if not can_place:
                    continue

                options.append(
                    _Probe(
                        row=row,
                        col=col,
                        direction=direction,
                    )
                )

    if not options:
        return None
    return rng.choice(options)


def _attempt_layout(
    candidates: Sequence[_Candidate],
    target_words: int,
    candidate_pool_size: int,
    rng: random.Random,
) -> list[_Placement]:
    def _pick_candidate_uniform_by_length(pool: Sequence[_Candidate]) -> _Candidate:
        buckets: dict[int, list[_Candidate]] = {}
        for item in pool:
            buckets.setdefault(len(item.answer), []).append(item)
        chosen_length = rng.choice(list(buckets.keys()))
        return rng.choice(buckets[chosen_length])

    def _pick_option_uniform_by_length(
        options: Sequence[tuple[_Candidate, _Probe]],
    ) -> tuple[_Candidate, _Probe]:
        buckets: dict[int, list[tuple[_Candidate, _Probe]]] = {}
        for option in options:
            candidate, _ = option
            buckets.setdefault(len(candidate.answer), []).append(option)
        chosen_length = rng.choice(list(buckets.keys()))
        return rng.choice(buckets[chosen_length])

    candidate_pool = list(candidates)
    rng.shuffle(candidate_pool)
    if candidate_pool_size > 0:
        candidate_pool = candidate_pool[: min(candidate_pool_size, len(candidate_pool))]

    if not candidate_pool:
        return []

    seed_candidate = _pick_candidate_uniform_by_length(candidate_pool)
    placements: list[_Placement] = [
        _Placement(
            answer=seed_candidate.answer,
            clue=seed_candidate.clue,
            hints=seed_candidate.hints,
            row=0,
            col=0,
            direction="across",
        )
    ]
    grid: dict[tuple[int, int], _Cell] = {}
    _apply_placement(grid, placements[0])
    used = {seed_candidate.answer}

    while len(placements) < target_words:
        remaining_candidates = [candidate for candidate in candidate_pool if candidate.answer not in used]
        rng.shuffle(remaining_candidates)

        placeable_options: list[tuple[_Candidate, _Probe]] = []
        for candidate in remaining_candidates:
            if candidate.answer in used:
                continue
            probe = _random_probe(candidate, grid, rng)
            if probe is None:
                continue
            placeable_options.append((candidate, probe))

        if not placeable_options:
            break

        picked = _pick_option_uniform_by_length(placeable_options)
        candidate, probe = picked
        placement = _Placement(
            answer=candidate.answer,
            clue=candidate.clue,
            hints=candidate.hints,
            row=probe.row,
            col=probe.col,
            direction=probe.direction,
        )
        _apply_placement(grid, placement)
        placements.append(placement)
        used.add(candidate.answer)

    return placements


def _placement_cells(placement: _Placement) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    is_across = placement.direction == "across"
    for offset in range(len(placement.answer)):
        row = placement.row + (0 if is_across else offset)
        col = placement.col + (offset if is_across else 0)
        coords.append((row, col))
    return coords


def _to_payload(placements: Sequence[_Placement]) -> dict[str, object]:
    used_cells = [coord for placement in placements for coord in _placement_cells(placement)]
    min_row = min(row for row, _ in used_cells)
    min_col = min(col for _, col in used_cells)

    normalized: list[_Placement] = []
    for placement in placements:
        normalized.append(
            _Placement(
                answer=placement.answer,
                clue=placement.clue,
                hints=placement.hints,
                row=placement.row - min_row,
                col=placement.col - min_col,
                direction=placement.direction,
            )
        )

    max_row = max(row for placement in normalized for row, _ in _placement_cells(placement))
    max_col = max(col for placement in normalized for _, col in _placement_cells(placement))

    rows = max_row + 1
    cols = max_col + 1
    grid = [["" for _ in range(cols)] for _ in range(rows)]

    for placement in normalized:
        for offset, letter in enumerate(placement.answer):
            row = placement.row + (0 if placement.direction == "across" else offset)
            col = placement.col + (offset if placement.direction == "across" else 0)
            grid[row][col] = letter

    starts = sorted({(placement.row, placement.col) for placement in normalized})
    numbering: dict[tuple[int, int], int] = {}
    for idx, point in enumerate(starts, start=1):
        numbering[point] = idx

    def _word_payload(placement: _Placement) -> dict[str, object]:
        number = numbering[(placement.row, placement.col)]
        prefix = "A" if placement.direction == "across" else "D"
        cells = [[row, col] for row, col in _placement_cells(placement)]
        return {
            "id": f"{prefix}{number}",
            "number": number,
            "direction": placement.direction,
            "row": placement.row,
            "col": placement.col,
            "answer": placement.answer,
            "clue": placement.clue,
            "hints": list(placement.hints),
            "length": len(placement.answer),
            "cells": cells,
        }

    words = [_word_payload(placement) for placement in normalized]
    across = sorted((word for word in words if word["direction"] == "across"), key=lambda item: item["number"])
    down = sorted((word for word in words if word["direction"] == "down"), key=lambda item: item["number"])

    return {
        "rows": rows,
        "cols": cols,
        "grid": grid,
        "words": words,
        "across": across,
        "down": down,
    }


def build_crossword_puzzle(
    entries: Sequence[WordEntry],
    *,
    target_words: int = 10,
    min_word_length: int = 2,
    max_word_length: int = 20,
    attempts: int = 80,
    candidate_pool_size: int = 300,
    seed: int | None = None,
) -> dict[str, object] | None:
    """Build a crossword puzzle payload from the loaded vocabulary entries."""
    target_words = max(3, min(target_words, 20))
    candidates = _build_candidates(entries, min_word_length=min_word_length, max_word_length=max_word_length)
    if len(candidates) < 3:
        return None

    master_rng = random.Random(seed)
    best: list[_Placement] = []

    for _ in range(max(1, attempts)):
        attempt_rng = random.Random(master_rng.randint(0, 10_000_000))
        placements = _attempt_layout(
            candidates=candidates,
            target_words=target_words,
            candidate_pool_size=candidate_pool_size,
            rng=attempt_rng,
        )
        if len(placements) > len(best):
            best = placements
        if len(best) >= target_words:
            break

    if len(best) < 3:
        return None

    # A crossword needs both clue directions to feel complete.
    has_across = any(placement.direction == "across" for placement in best)
    has_down = any(placement.direction == "down" for placement in best)
    if not (has_across and has_down):
        return None

    return _to_payload(best)
