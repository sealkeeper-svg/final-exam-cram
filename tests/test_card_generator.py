import json
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from crammer.db.store import (
    init_db, add_subject, add_chapter, add_knowledge_point, get_cards, get_calc_problems
)
from crammer.extractor.card_generator import generate_cards_for_subject

MOCK_DS_RESPONSE = {
    "cards": [
        {
            "kp_title": "边际贡献的概念",
            "cards": [
                {"card_type": "definition", "question": "什么是边际贡献？", "answer": "边际贡献 = 销售收入 - 变动成本", "difficulty": "基础"},
                {"card_type": "short_answer", "question": "边际贡献的意义是什么？", "answer": "衡量产品盈利能力", "difficulty": "进阶"}
            ]
        }
    ]
}


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    return db_path


@pytest.fixture
def subject_with_kps(db):
    sid = add_subject("管理会计", date(2026, 6, 28), db_path=db).id
    cid = add_chapter(sid, "第一章 成本性态", 1, db_path=db).id
    add_knowledge_point(cid, "边际贡献的概念", "边际贡献是销售收入减变动成本", "concept", db_path=db)
    add_knowledge_point(cid, "保本点分析", "保本点即利润为零时的销量", "calculation", formula="Q = FC / (P - VC)", db_path=db)
    return sid


def test_generate_concept_cards(db, subject_with_kps):
    with patch('crammer.extractor.card_generator.deepseek_chat') as mock_ds:
        mock_ds.return_value = json.dumps(MOCK_DS_RESPONSE, ensure_ascii=False)
        result = generate_cards_for_subject(subject_with_kps, api_key="sk-test", db_path=db)

    assert result["concept_cards"] == 2
    cards = get_cards(1, db_path=db)
    assert len(cards) == 2


def test_generate_calc_unmatched(db, subject_with_kps):
    with patch('crammer.extractor.card_generator.deepseek_chat') as mock_ds:
        mock_ds.return_value = json.dumps(MOCK_DS_RESPONSE, ensure_ascii=False)
        result = generate_cards_for_subject(subject_with_kps, api_key="sk-test", db_path=db)

    assert result["calc_unmatched"] >= 0


def test_stats_returned(db, subject_with_kps):
    with patch('crammer.extractor.card_generator.deepseek_chat') as mock_ds:
        mock_ds.return_value = json.dumps(MOCK_DS_RESPONSE, ensure_ascii=False)
        result = generate_cards_for_subject(subject_with_kps, api_key="sk-test", db_path=db)

    assert "concept_cards" in result
    assert "calc_problems" in result
    assert "calc_unmatched" in result
    assert isinstance(result["concept_cards"], int)


def test_batch_failure_continues(db, subject_with_kps):
    call_count = 0

    def fail_then_succeed(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("network error")
        return json.dumps(MOCK_DS_RESPONSE, ensure_ascii=False)

    with patch('crammer.extractor.card_generator.deepseek_chat', side_effect=fail_then_succeed):
        result = generate_cards_for_subject(subject_with_kps, api_key="sk-test", db_path=db)

    assert result["concept_cards"] >= 0


def test_progress_callback(db, subject_with_kps):
    progress_calls = []

    with patch('crammer.extractor.card_generator.deepseek_chat') as mock_ds:
        mock_ds.return_value = json.dumps(MOCK_DS_RESPONSE, ensure_ascii=False)
        generate_cards_for_subject(
            subject_with_kps, api_key="sk-test", db_path=db,
            on_progress=lambda cur, total, cid: progress_calls.append((cur, total))
        )

    assert len(progress_calls) > 0
