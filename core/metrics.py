from __future__ import annotations

from datetime import date

from core.models import ReviewState, WordEntry


def due_words(word_list: list[str], states: dict[str, ReviewState]) -> list[str]:
    today = date.today()
    due = []
    for word in word_list:
        state = states.get(word.lower())
        if state and state.due_date <= today:
            due.append(word)
    return due


def accuracy_for_words(word_list: list[str], states: dict[str, ReviewState]) -> float:
    total_correct = 0
    total_incorrect = 0
    for word in word_list:
        state = states.get(word.lower())
        if not state:
            continue
        total_correct += state.correct_count
        total_incorrect += state.incorrect_count
    total = total_correct + total_incorrect
    if total == 0:
        return 0.0
    return total_correct / total


def weak_words(entries: list[WordEntry], states: dict[str, ReviewState], limit: int = 10) -> list[tuple[str, float]]:
    scored = []
    for entry in entries:
        state = states.get(entry.word.lower())
        if not state:
            continue
        scored.append((entry.word, state.accuracy(), state.lapse_count))
    scored.sort(key=lambda item: (item[1], -item[2]))
    return [(word, acc) for word, acc, _ in scored[:limit]]
