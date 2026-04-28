from datetime import datetime, timedelta

from core.deck_progress import (
    DeckSessionSettings,
    apply_outcome,
    build_deck_session,
    init_deck_state,
    select_due_words,
)


def test_apply_outcome_updates_interval_and_lapses():
    now = datetime(2024, 1, 1, 8, 0, 0)
    state = init_deck_state("alpha", now)
    updated = apply_outcome(state, "again", now)
    assert updated.interval_days == 1
    assert updated.lapses == 1
    assert updated.next_due_at >= now

    reviewed = apply_outcome(updated, "good", now + timedelta(days=1))
    assert reviewed.interval_days >= 1
    assert reviewed.state in {"review", "mastered"}


def test_select_due_words_filters_by_due_time():
    now = datetime(2024, 1, 1, 8, 0, 0)
    due = init_deck_state("due", now)
    due = apply_outcome(due, "good", now)
    due = due.__class__(**{**due.__dict__, "next_due_at": now - timedelta(hours=1)})
    future = init_deck_state("future", now)
    future = apply_outcome(future, "good", now)

    states = {"due": due, "future": future}
    selected = select_due_words(["Due", "Future", "New"], states, now)
    assert selected == ["Due"]


def test_build_deck_session_orders_due_before_new():
    now = datetime(2024, 1, 1, 8, 0, 0)
    due_state = apply_outcome(init_deck_state("due", now), "good", now)
    due_state = due_state.__class__(**{**due_state.__dict__, "next_due_at": now - timedelta(hours=1)})
    states = {"due": due_state}
    settings = DeckSessionSettings(new_words_per_session=2, max_review_per_session=5, mix_new_and_review=True)
    session = build_deck_session(["Due", "New1", "New2"], states, settings, now)
    assert session[0] == "Due"
    assert session[1:] == ["New1", "New2"]
