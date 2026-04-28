from __future__ import annotations

from core.crossword import build_crossword_puzzle
from core.models import WordEntry


def _sample_entries() -> list[WordEntry]:
    return [
        WordEntry(word="abate", meaning="to become less intense"),
        WordEntry(word="beta", meaning="a test release"),
        WordEntry(word="eager", meaning="keenly expecting something"),
        WordEntry(word="grace", meaning="elegance of movement"),
        WordEntry(word="react", meaning="to respond to a stimulus"),
        WordEntry(word="trace", meaning="to follow or discover"),
        WordEntry(word="cater", meaning="to provide what is needed"),
        WordEntry(word="crate", meaning="a large packing box"),
        WordEntry(word="caret", meaning="proofreading insertion mark"),
        WordEntry(word="taker", meaning="one who takes"),
        WordEntry(word="raven", meaning="a large black bird"),
        WordEntry(word="naive", meaning="showing lack of experience"),
    ]


def test_build_crossword_puzzle_returns_valid_structure() -> None:
    puzzle = build_crossword_puzzle(
        _sample_entries(),
        target_words=8,
        seed=42,
        attempts=120,
        candidate_pool_size=80,
    )

    assert puzzle is not None
    assert puzzle["rows"] > 0
    assert puzzle["cols"] > 0
    assert puzzle["across"]
    assert puzzle["down"]

    words = puzzle["words"]
    grid = puzzle["grid"]
    assert 3 <= len(words) <= 8

    cell_usage: dict[tuple[int, int], int] = {}
    for word in words:
        assert word["answer"]
        assert word["clue"]
        assert isinstance(word["hints"], list)
        assert len(word["hints"]) == 2
        assert all(isinstance(item, str) and item for item in word["hints"])
        assert len(word["cells"]) == word["length"]
        for index, (row, col) in enumerate(word["cells"]):
            assert grid[row][col] == word["answer"][index]
            cell_usage[(row, col)] = cell_usage.get((row, col), 0) + 1

    assert any(count > 1 for count in cell_usage.values())


def test_build_crossword_puzzle_is_deterministic_for_seed() -> None:
    first = build_crossword_puzzle(_sample_entries(), target_words=7, seed=7)
    second = build_crossword_puzzle(_sample_entries(), target_words=7, seed=7)

    assert first == second


def test_build_crossword_puzzle_returns_none_when_not_enough_candidates() -> None:
    entries = [
        WordEntry(word="a-b", meaning="contains punctuation and becomes too short"),
        WordEntry(word="cat", meaning="short word"),
        WordEntry(word="valid", meaning=None),
    ]

    puzzle = build_crossword_puzzle(entries, target_words=6, seed=99)

    assert puzzle is None
