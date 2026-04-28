from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

from core.models import DeckReviewState


DEFAULT_EASE = 2.5
MIN_EASE = 1.3
MASTERED_INTERVAL_DAYS = 21
MASTERED_MIN_REVIEWS = 3


@dataclass(frozen=True)
class DeckSessionSettings:
    new_words_per_session: int = 20
    max_review_per_session: int = 50
    mix_new_and_review: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "new_words_per_session": self.new_words_per_session,
            "max_review_per_session": self.max_review_per_session,
            "mix_new_and_review": self.mix_new_and_review,
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> "DeckSessionSettings":
        return DeckSessionSettings(
            new_words_per_session=int(data.get("new_words_per_session", 20)),
            max_review_per_session=int(data.get("max_review_per_session", 50)),
            mix_new_and_review=bool(data.get("mix_new_and_review", True)),
        )


def _now(value: datetime | None) -> datetime:
    return value or datetime.now()


def init_deck_state(word_id: str, now: datetime | None = None) -> DeckReviewState:
    return DeckReviewState(word_id=word_id, ease=DEFAULT_EASE, last_reviewed_at=None, next_due_at=None)


def is_due(state: DeckReviewState | None, now: datetime | None = None) -> bool:
    if not state:
        return False
    if state.state == "suspended":
        return False
    if state.state not in {"learning", "review", "mastered"}:
        return False
    current = _now(now)
    return state.next_due_at is not None and state.next_due_at <= current


def is_new(state: DeckReviewState | None) -> bool:
    return not state or state.state == "new"


def apply_outcome(
    state: DeckReviewState, outcome: str, now: datetime | None = None
) -> DeckReviewState:
    current = _now(now)
    outcome = outcome.lower()
    ease = state.ease
    interval = state.interval_days

    first_review = state.reviews == 0
    if first_review:
        if outcome == "again":
            interval = 1
            ease -= 0.2
        elif outcome == "hard":
            interval = 1
            ease -= 0.15
        elif outcome == "good":
            interval = 2
        elif outcome == "easy":
            interval = 4
            ease += 0.15
    else:
        if outcome == "again":
            interval = 1
            ease -= 0.2
        elif outcome == "hard":
            interval = max(1, int(interval * 1.2))
            ease -= 0.15
        elif outcome == "good":
            interval = max(1, int(interval * ease))
        elif outcome == "easy":
            interval = max(2, int(interval * (ease + 0.3)))
            ease += 0.15

    ease = max(MIN_EASE, ease)
    next_due = current + timedelta(days=interval)

    if outcome in {"again", "hard"}:
        new_state = "learning"
    else:
        new_state = "review"

    reviews = state.reviews + 1
    if interval >= MASTERED_INTERVAL_DAYS and reviews >= MASTERED_MIN_REVIEWS and outcome in {"good", "easy"}:
        new_state = "mastered"

    return DeckReviewState(
        word_id=state.word_id,
        state=new_state,
        last_reviewed_at=current,
        next_due_at=next_due,
        interval_days=interval,
        ease=ease,
        reviews=reviews,
        lapses=state.lapses + (1 if outcome == "again" else 0),
        last_outcome=outcome,
    )


def select_due_words(
    word_ids: Iterable[str],
    states: dict[str, DeckReviewState],
    now: datetime | None = None,
    limit: int | None = None,
) -> list[str]:
    due = [word for word in word_ids if is_due(states.get(word.lower()), now)]
    if limit is not None:
        return due[:limit]
    return due


def select_new_words(
    word_ids: Iterable[str],
    states: dict[str, DeckReviewState],
    limit: int | None = None,
) -> list[str]:
    new_words = [word for word in word_ids if is_new(states.get(word.lower()))]
    if limit is not None:
        return new_words[:limit]
    return new_words


def build_deck_session(
    word_ids: list[str],
    states: dict[str, DeckReviewState],
    settings: DeckSessionSettings,
    now: datetime | None = None,
    review_only: bool = False,
) -> list[str]:
    due = select_due_words(word_ids, states, now, limit=settings.max_review_per_session)
    if review_only:
        return due
    new_words = select_new_words(word_ids, states, limit=settings.new_words_per_session)
    return [*due, *new_words]


def deck_progress_counts(
    word_ids: Iterable[str], states: dict[str, DeckReviewState], now: datetime | None = None
) -> dict[str, int]:
    counts = {"new": 0, "learning": 0, "review": 0, "mastered": 0, "suspended": 0, "due": 0}
    for word in word_ids:
        state = states.get(word.lower())
        if not state:
            counts["new"] += 1
            continue
        state_name = state.state if state.state in counts else "learning"
        counts[state_name] += 1
        if is_due(state, now):
            counts["due"] += 1
    return counts
