from datetime import date, timedelta
from crammer.scheduler.spaced_repetition import next_review_date


def test_pass_doubles_interval():
    exam = date(2026, 7, 1)
    result = next_review_date("pass", 2, exam)
    assert result == date.today() + timedelta(days=4)


def test_fail_resets_to_one():
    exam = date(2026, 7, 1)
    result = next_review_date("fail", 2, exam)
    assert result == date.today() + timedelta(days=1)


def test_exam_day_anchor():
    exam = date.today() + timedelta(days=3)
    result = next_review_date("pass", 8, exam)
    assert result == exam


def test_interval_cap_at_16():
    exam = date.today() + timedelta(days=365)
    result = next_review_date("pass", 16, exam)
    assert result == date.today() + timedelta(days=16)


def test_first_review_interval_zero():
    exam = date(2026, 7, 1)
    result = next_review_date("pass", 0, exam)
    assert result == date.today() + timedelta(days=1)
