import pytest
from datetime import date
from crammer.db.store import init_db, add_subject, add_chapter, add_knowledge_point, add_card
from crammer.review.guided_learning import (
    build_learning_paths, get_path_by_id, format_step_for_display,
    LearningPath, LearningStep
)


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    return db_path


@pytest.fixture
def subject_with_cards(db):
    sid = add_subject("管理会计", date(2026, 6, 28), db_path=db).id
    for i, ch_title in enumerate(["成本性态分析", "本量利分析", "全面预算"], 1):
        cid = add_chapter(sid, ch_title, i, db_path=db).id
        kp = add_knowledge_point(cid, f"知识点{i}", f"这是第{i}章的核心内容。需要理解。", "concept", db_path=db)
        add_card(kp.id, "definition", f"问题{i}？", f"答案{i}", db_path=db)
    return sid


def test_build_paths(db, subject_with_cards):
    paths = build_learning_paths(subject_with_cards, db_path=db)
    assert len(paths) > 0


def test_path_structure(db, subject_with_cards):
    paths = build_learning_paths(subject_with_cards, db_path=db)
    for p in paths:
        assert p.title
        assert p.description
        assert len(p.steps) > 0


def test_step_has_content(db, subject_with_cards):
    paths = build_learning_paths(subject_with_cards, db_path=db)
    for p in paths:
        for step in p.steps:
            assert step.explanation
            assert step.title


def test_no_cards_returns_empty(db):
    sid = add_subject("经济政策", date(2026, 7, 1), db_path=db).id
    add_chapter(sid, "第一章", 1, db_path=db)
    paths = build_learning_paths(sid, db_path=db)
    assert paths == []


def test_get_path_by_id(db, subject_with_cards):
    paths = build_learning_paths(subject_with_cards, db_path=db)
    assert len(paths) > 0
    found = get_path_by_id(subject_with_cards, paths[0].path_id, db_path=db)
    assert found is not None
    assert found.title == paths[0].title
    assert get_path_by_id(subject_with_cards, "nonexistent", db_path=db) is None


def test_format_step(db, subject_with_cards):
    paths = build_learning_paths(subject_with_cards, db_path=db)
    step = paths[0].steps[0]
    result = format_step_for_display(step)
    assert len(result) > 0
    assert step.title in result
