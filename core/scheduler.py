from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta

from core.models import ReviewState


DEFAULT_EASE = 2.5
MIN_EASE = 1.3


def init_state(word: str) -> ReviewState:
    today = date.today()
    return ReviewState(word=word, due_date=today, interval_days=0, ease_factor=DEFAULT_EASE)


def schedule_review(state: ReviewState, rating: str) -> ReviewState:
    today = date.today()
    rating = rating.lower()
    ease = state.ease_factor
    interval = state.interval_days

    if state.review_count == 0:
        if rating == "again":
            interval = 1
            ease -= 0.2
        elif rating == "hard":
            interval = 1
            ease -= 0.15
        elif rating == "good":
            interval = 2
        elif rating == "easy":
            interval = 4
            ease += 0.15
    else:
        if rating == "again":
            interval = 1
            ease -= 0.2
        elif rating == "hard":
            interval = max(1, int(interval * 1.2))
            ease -= 0.15
        elif rating == "good":
            interval = max(1, int(interval * ease))
        elif rating == "easy":
            interval = max(2, int(interval * (ease + 0.3)))
            ease += 0.15

    ease = max(MIN_EASE, ease)
    due_date = today + timedelta(days=interval)

    correct = rating in {"good", "easy"}
    incorrect = rating in {"again", "hard"}

    return replace(
        state,
        due_date=due_date,
        interval_days=interval,
        ease_factor=ease,
        last_review=today,
        review_count=state.review_count + 1,
        lapse_count=state.lapse_count + (1 if rating == "again" else 0),
        correct_count=state.correct_count + (1 if correct else 0),
        incorrect_count=state.incorrect_count + (1 if incorrect else 0),
    )
