import pytest
from datetime import date
from crammer.db.store import init_db, add_subject, add_chapter, add_knowledge_point, add_card
from crammer.scheduler.spaced_repetition import get_due_cards, get_subject_dashboard, update_kp_after_review
from crammer.review.daily_review import start_daily_review, record_review_result


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    return db_path


@pytest.fixture
def subject_with_kp(db):
    sid = add_subject("管理会计", date(2026, 6, 28), db_path=db).id
    cid = add_chapter(sid, "第一章", 1, db_path=db).id
    kp = add_knowledge_point(cid, "边际贡献", "概念解释", "concept", db_path=db)
    add_card(kp.id, "definition", "问题", "答案", db_path=db)
    return sid, date(2026, 6, 28)


def test_get_due_cards(db, subject_with_kp):
    sid, _ = subject_with_kp
    due = get_due_cards(sid, db_path=db)
    assert len(due) > 0
    card, kp = due[0]
    assert card.question == "问题"


def test_get_dashboard(db, subject_with_kp):
    sid, _ = subject_with_kp
    dash = get_subject_dashboard(sid, db_path=db)
    assert dash["total_kps"] == 1
    assert dash["total_cards"] == 1
    assert "due_cards_today" in dash
    assert "days_until_exam" in dash


def test_update_kp_after_review_pass(db, subject_with_kp):
    sid, exam = subject_with_kp
    due = get_due_cards(sid, db_path=db)
    card, kp = due[0]
    update_kp_after_review(kp.id, "pass", exam, card_id=card.id, db_path=db)
    due_after = get_due_cards(sid, db_path=db)
    assert len(due_after) == 0


def test_update_kp_after_review_fail(db, subject_with_kp):
    sid, exam = subject_with_kp
    due = get_due_cards(sid, db_path=db)
    card, kp = due[0]
    update_kp_after_review(kp.id, "fail", exam, card_id=card.id, db_path=db)
    from crammer.db.store import get_error_bookmarks
    bookmarks = get_error_bookmarks(resolved=False, db_path=db)
    assert len(bookmarks) == 1


def test_start_daily_review(db, subject_with_kp):
    sid, _ = subject_with_kp
    session = start_daily_review(sid, db_path=db)
    assert session["subject_name"] == "管理会计"
    assert "dashboard" in session
    assert "cards" in session
    assert session["total_due"] > 0
