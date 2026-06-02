import pytest
from datetime import date
from crammer.db.store import init_db, add_subject, add_chapter, add_knowledge_point, add_card, add_review_log, upsert_error_bookmark
from crammer.review.cram_mode import get_cram_flash_cards, get_key_points, get_error_redo_cards


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    return db_path


@pytest.fixture
def populated_subject(db):
    sid = add_subject("管理会计", date(2026, 6, 28), db_path=db).id
    cid = add_chapter(sid, "第一章", 1, db_path=db).id
    kp1 = add_knowledge_point(cid, "边际贡献", "核心概念解释内容", "concept", formula="CM = P - VC", db_path=db)
    add_card(kp1.id, "definition", "什么是边际贡献？", "答案1", db_path=db)
    add_card(kp1.id, "short_answer", "边际贡献的意义？", "答案2", db_path=db)
    kp2 = add_knowledge_point(cid, "保本点", "计算内容", "calculation", formula="Q = FC/(P-VC)", db_path=db)
    add_card(kp2.id, "definition", "保本点如何计算？", "答案3", db_path=db)
    return sid


def test_flash_cards(db, populated_subject):
    cards = get_cram_flash_cards(populated_subject, db_path=db)
    assert len(cards) > 0
    for c in cards:
        assert "question" in c
        assert "answer" in c
        assert "mastery" in c


def test_key_points(db, populated_subject):
    result = get_key_points(populated_subject, db_path=db)
    assert "formulas" in result
    assert "core_concepts" in result
    assert "high_error_kps" in result


def test_error_redo(db, populated_subject):
    chapters = __import__('crammer.db.store', fromlist=['get_chapters']).get_chapters(populated_subject, db_path=db)
    kps = __import__('crammer.db.store', fromlist=['get_knowledge_points']).get_knowledge_points(chapters[0].id, db_path=db)
    cards = __import__('crammer.db.store', fromlist=['get_cards']).get_cards(kps[0].id, db_path=db)

    upsert_error_bookmark(card_id=cards[0].id, db_path=db)

    result = get_error_redo_cards(populated_subject, db_path=db)
    assert len(result) > 0
    assert result[0]["error_count"] >= 1
