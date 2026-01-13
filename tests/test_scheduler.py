from datetime import date

from core.scheduler import init_state, schedule_review


def test_schedule_review_increases_interval():
    state = init_state("abate")
    reviewed = schedule_review(state, "good")
    assert reviewed.interval_days >= 2
    assert reviewed.due_date >= date.today()


def test_schedule_review_again_resets_interval():
    state = init_state("abate")
    state.interval_days = 10
    reviewed = schedule_review(state, "again")
    assert reviewed.interval_days == 1
    assert reviewed.lapse_count == 1
