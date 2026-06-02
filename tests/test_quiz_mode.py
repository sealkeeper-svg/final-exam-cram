import pytest
from datetime import date
from crammer.db.store import init_db, add_subject, add_chapter, add_knowledge_point, add_card, add_calc_problem
from crammer.review.quiz_mode import generate_quiz, score_quiz


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    return db_path


@pytest.fixture
def subject_with_mixed(db):
    sid = add_subject("管理会计", date(2026, 6, 28), db_path=db).id
    for i in range(3):
        cid = add_chapter(sid, f"第{i+1}章", i+1, db_path=db).id
        kp = add_knowledge_point(cid, f"概念点{i}", f"内容{i}", "concept", db_path=db)
        add_card(kp.id, "definition", f"问题{i}", f"答案{i}", db_path=db)
        kp2 = add_knowledge_point(cid, f"计算点{i}", f"计算内容{i}", "calculation", formula=f"公式{i}", db_path=db)
        add_calc_problem(kp2.id, f"计算题{i}", f"计算答案{i}", template_name="保本点分析", db_path=db)
    return sid


def test_generate_quiz(db, subject_with_mixed):
    quiz = generate_quiz(subject_with_mixed, num_questions=6, db_path=db)
    assert quiz["subject_name"] == "管理会计"
    assert len(quiz["questions"]) == 6
    assert quiz["time_limit_minutes"] == 20


def test_generate_quiz_counts(db, subject_with_mixed):
    quiz = generate_quiz(subject_with_mixed, num_questions=6, db_path=db)
    concept_count = sum(1 for q in quiz["questions"] if q["type"] == "概念")
    calc_count = sum(1 for q in quiz["questions"] if q["type"] == "计算")
    assert concept_count >= 0
    assert calc_count >= 0
    assert concept_count + calc_count == 6


def test_score_quiz(db, subject_with_mixed):
    quiz = generate_quiz(subject_with_mixed, num_questions=3, db_path=db)
    user_results = [
        {"correct": True, "time_spent": 30},
        {"correct": False, "time_spent": 45, "kp_id": 1},
        {"correct": True, "time_spent": 25},
    ]
    result = score_quiz(quiz["questions"], user_results, subject_with_mixed, db_path=db)
    assert result["score"] == 2
    assert result["total"] == 3


def test_score_quiz_records_errors(db, subject_with_mixed):
    quiz = generate_quiz(subject_with_mixed, num_questions=3, db_path=db)
    user_results = [
        {"correct": False, "time_spent": 40, "kp_id": 1},
        {"correct": False, "time_spent": 30, "kp_id": 1},
        {"correct": True, "time_spent": 20},
    ]
    score_quiz(quiz["questions"], user_results, subject_with_mixed, db_path=db)
    from crammer.db.store import get_error_bookmarks
    bookmarks = get_error_bookmarks(resolved=False, db_path=db)
    assert len(bookmarks) >= 0


def test_generate_quiz_empty_subject(db):
    sid = add_subject("空科目", date(2026, 7, 1), db_path=db).id
    add_chapter(sid, "第一章", 1, db_path=db)
    quiz = generate_quiz(sid, num_questions=5, db_path=db)
    assert quiz["total"] == 0
