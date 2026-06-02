import json
import os
import tempfile
from datetime import date
from unittest.mock import patch

from crammer.db.store import init_db, add_subject, get_chapters, get_knowledge_points
from crammer.extractor.knowledge_tree import (
    build_knowledge_tree,
    confirm_chapters,
    extract_metadata,
)


class MockChunk:
    def __init__(self, chunk_id, text, page_range=(1, 2), source_file="test.pdf"):
        self.chunk_id = chunk_id
        self.text = text
        self.page_range = page_range
        self.source_file = source_file
        self.has_tables = False
        self.tables_md = []


MOCK_SINGLE_BATCH = json.dumps(
    {
        "chapters": [
            {
                "title": "第一章 成本性态分析",
                "order": 1,
                "sections": [
                    {
                        "title": "成本按性态分类",
                        "knowledge_points": [
                            {
                                "name": "固定成本的定义与特征",
                                "type": "concept",
                                "content": "固定成本是指在一定时期和一定业务量范围内，总额不随业务量变动而变动的成本。",
                                "formula": None,
                            },
                            {
                                "name": "变动成本的定义与特征",
                                "type": "concept",
                                "content": "变动成本是指总额随业务量变动而成正比例变动的成本。",
                                "formula": None,
                            },
                        ],
                    }
                ],
            },
            {
                "title": "第二章 本量利分析",
                "order": 2,
                "sections": [
                    {
                        "title": "盈亏平衡点",
                        "knowledge_points": [
                            {
                                "name": "盈亏平衡点计算公式",
                                "type": "calculation",
                                "content": "盈亏平衡点是指企业利润为零时的销售量。",
                                "formula": "盈亏平衡点销售量 = 固定成本 / (单价 - 单位变动成本)",
                            }
                        ],
                    }
                ],
            },
        ]
    },
    ensure_ascii=False,
)


def test_build_tree_mock():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        init_db(db_path)
        subject = add_subject("管理会计", exam_date=date(2026, 6, 20), db_path=db_path)

        chunks = [
            MockChunk("chunk_001", "课件内容关于成本性态..."),
            MockChunk("chunk_002", "课件内容关于本量利分析..."),
        ]

        progress_calls = []

        with patch("crammer.extractor.knowledge_tree.deepseek_chat") as mock:
            mock.return_value = MOCK_SINGLE_BATCH
            result = build_knowledge_tree(
                chunks,
                "管理会计",
                subject_id=subject.id,
                db_path=db_path,
                on_progress=lambda c, t, cid: progress_calls.append((c, t, cid)),
            )

        assert "chapters" in result
        assert len(result["chapters"]) == 2
        assert result["chapters"][0]["title"] == "第一章 成本性态分析"
        assert result["chapters"][0]["order"] == 1
        assert "_chapter_id" in result["chapters"][0]
        assert len(result["chapters"][0]["sections"]) == 1
        assert (
            result["chapters"][0]["sections"][0]["knowledge_points"][0]["name"]
            == "固定成本的定义与特征"
        )
        assert (
            result["chapters"][0]["sections"][0]["knowledge_points"][0]["type"]
            == "concept"
        )

        assert result["chapters"][1]["title"] == "第二章 本量利分析"
        assert result["chapters"][1]["order"] == 2

        chapters = get_chapters(subject.id, db_path=db_path)
        assert len(chapters) == 2
        assert chapters[0].title == "第一章 成本性态分析"
        assert chapters[1].title == "第二章 本量利分析"

        kps = get_knowledge_points(chapters[0].id, db_path=db_path)
        assert len(kps) == 2
        assert kps[0].title == "固定成本的定义与特征"
        assert kps[0].type == "concept"
        assert kps[0].content is not None
        assert kps[0].formula is None
        assert kps[1].title == "变动成本的定义与特征"
        assert kps[1].type == "concept"

        kps_ch2 = get_knowledge_points(chapters[1].id, db_path=db_path)
        assert len(kps_ch2) == 1
        assert kps_ch2[0].type == "calculation"
        assert kps_ch2[0].formula is not None

        assert len(progress_calls) == 1
        assert progress_calls[0] == (1, 1, "chunk_001")

    finally:
        os.unlink(db_path)


def test_build_tree_multi_batch():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        init_db(db_path)
        subject = add_subject("测试科目", exam_date=date(2026, 6, 20), db_path=db_path)

        chunks = [MockChunk(f"chunk_{i:03d}", f"内容{i}") for i in range(1, 8)]

        batch1_response = json.dumps(
            {
                "chapters": [
                    {
                        "title": "第一章",
                        "order": 1,
                        "sections": [
                            {
                                "title": "第一节",
                                "knowledge_points": [
                                    {
                                        "name": "知识点A",
                                        "type": "concept",
                                        "content": "内容A",
                                        "formula": None,
                                    }
                                ],
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        )

        batch2_response = json.dumps(
            {
                "chapters": [
                    {
                        "title": "第二章",
                        "order": 2,
                        "sections": [
                            {
                                "title": "第一节",
                                "knowledge_points": [
                                    {
                                        "name": "知识点B",
                                        "type": "calculation",
                                        "content": "内容B",
                                        "formula": "x = y + z",
                                    }
                                ],
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        )

        with patch("crammer.extractor.knowledge_tree.deepseek_chat") as mock:
            mock.side_effect = [batch1_response, batch2_response]
            result = build_knowledge_tree(
                chunks, "测试科目", subject_id=subject.id, db_path=db_path
            )

        assert len(result["chapters"]) == 2
        assert result["chapters"][0]["title"] == "第一章"
        assert result["chapters"][1]["title"] == "第二章"

        chapters = get_chapters(subject.id, db_path=db_path)
        assert len(chapters) == 2

    finally:
        os.unlink(db_path)


def test_build_tree_batch_failure_continues():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        init_db(db_path)
        subject = add_subject("测试科目", exam_date=date(2026, 6, 20), db_path=db_path)

        chunks = [MockChunk(f"chunk_{i:03d}", f"内容{i}") for i in range(1, 8)]

        batch2_response = json.dumps(
            {
                "chapters": [
                    {
                        "title": "第一章",
                        "order": 1,
                        "sections": [
                            {
                                "title": "第一节",
                                "knowledge_points": [
                                    {
                                        "name": "知识点X",
                                        "type": "concept",
                                        "content": "内容X",
                                        "formula": None,
                                    }
                                ],
                            }
                        ],
                    }
                ]
            },
            ensure_ascii=False,
        )

        with patch("crammer.extractor.knowledge_tree.deepseek_chat") as mock:
            mock.side_effect = [RuntimeError("API error"), batch2_response]
            result = build_knowledge_tree(
                chunks, "测试科目", subject_id=subject.id, db_path=db_path
            )

        assert len(result["chapters"]) == 1
        assert result["chapters"][0]["title"] == "第一章"

        chapters = get_chapters(subject.id, db_path=db_path)
        assert len(chapters) == 1

    finally:
        os.unlink(db_path)


def test_confirm_chapters():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        init_db(db_path)
        subject = add_subject("测试科目", exam_date=date(2026, 6, 20), db_path=db_path)

        from crammer.db.store import add_chapter

        ch1 = add_chapter(subject.id, "第一章", 1, db_path=db_path)
        ch2 = add_chapter(subject.id, "第二章", 2, db_path=db_path)
        ch3 = add_chapter(subject.id, "第三章", 3, db_path=db_path)
        ch4 = add_chapter(subject.id, "第四章", 4, db_path=db_path)

        tree = {
            "chapters": [
                {"title": "第一章", "order": 1, "_chapter_id": ch1.id, "sections": []},
                {"title": "第二章", "order": 2, "_chapter_id": ch2.id, "sections": []},
                {"title": "第三章", "order": 3, "_chapter_id": ch3.id, "sections": []},
                {"title": "第四章", "order": 4, "_chapter_id": ch4.id, "sections": []},
            ],
            "_db_path": db_path,
        }

        result = confirm_chapters(tree, [0, 2])

        assert len(result["chapters"]) == 2
        assert result["chapters"][0]["title"] == "第一章"
        assert result["chapters"][1]["title"] == "第三章"

        active_chapters = get_chapters(subject.id, db_path=db_path)
        assert len(active_chapters) == 2
        active_titles = {c.title for c in active_chapters}
        assert active_titles == {"第一章", "第三章"}

    finally:
        os.unlink(db_path)


def test_extract_metadata():
    tree = {
        "chapters": [
            {
                "title": "第一章",
                "order": 1,
                "sections": [
                    {
                        "title": "第一节",
                        "knowledge_points": [
                            {"name": "概念1", "type": "concept"},
                            {"name": "概念2", "type": "concept"},
                            {"name": "计算1", "type": "calculation"},
                        ],
                    },
                    {
                        "title": "第二节",
                        "knowledge_points": [
                            {"name": "概念3", "type": "concept"},
                        ],
                    },
                ],
            },
            {
                "title": "第二章",
                "order": 2,
                "sections": [
                    {
                        "title": "第一节",
                        "knowledge_points": [
                            {"name": "计算2", "type": "calculation"},
                            {"name": "计算3", "type": "calculation"},
                        ],
                    }
                ],
            },
        ]
    }

    meta = extract_metadata(tree)

    assert meta["chapter_count"] == 2
    assert meta["kp_count"] == 6
    assert meta["concept_count"] == 3
    assert meta["calculation_count"] == 3


def test_extract_metadata_empty():
    tree = {"chapters": []}
    meta = extract_metadata(tree)
    assert meta["chapter_count"] == 0
    assert meta["kp_count"] == 0
    assert meta["concept_count"] == 0
    assert meta["calculation_count"] == 0


def test_build_tree_api_key_from_config():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        init_db(db_path)
        subject = add_subject("测试科目", exam_date=date(2026, 6, 20), db_path=db_path)

        chunks = [MockChunk("chunk_001", "内容")]

        with patch("crammer.extractor.knowledge_tree.deepseek_chat") as mock_chat, \
             patch("crammer.extractor.knowledge_tree.get_api_key") as mock_key:
            mock_key.return_value = "sk-from-config"
            mock_chat.return_value = json.dumps({"chapters": []}, ensure_ascii=False)

            build_knowledge_tree(
                chunks, "测试科目", subject_id=subject.id, db_path=db_path
            )

            mock_key.assert_called_once()
            mock_chat.assert_called_once()
            call_args = mock_chat.call_args
            assert call_args[0][1] == "sk-from-config"

    finally:
        os.unlink(db_path)
