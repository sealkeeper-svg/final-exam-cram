import os
import pytest
from crammer.extractor.chunker import chunk_documents, scan_folder, Chunk


def _make_parsed(pages_data, filename="test.pdf"):
    pages = []
    for i, (text, tables) in enumerate(pages_data):
        pages.append(
            {"page_num": i + 1, "text": text, "tables": tables or []}
        )
    return {"pages": pages, "total_pages": len(pages), "source_file": filename}


def test_chunk_single_page():
    pf = _make_parsed([("Hello world", [])])
    chunks = chunk_documents([pf], max_chars=3000)
    assert len(chunks) == 1
    assert chunks[0].text == "Hello world"
    assert chunks[0].page_range == (1, 1)
    assert chunks[0].chunk_id == "chunk_001"


def test_chunk_merge_adjacent():
    pf = _make_parsed([("Short page 1", []), ("Short page 2", [])])
    chunks = chunk_documents([pf], max_chars=3000)
    assert len(chunks) == 1
    assert chunks[0].page_range == (1, 2)
    assert "Short page 1" in chunks[0].text
    assert "Short page 2" in chunks[0].text


def test_chunk_max_chars_split():
    pf = _make_parsed([("A" * 2000, []), ("B" * 2000, [])])
    chunks = chunk_documents([pf], max_chars=3000)
    assert len(chunks) == 2
    assert chunks[0].page_range == (1, 1)
    assert chunks[1].page_range == (2, 2)


def test_chunk_oversized_page():
    pf = _make_parsed([("X" * 5000, [])])
    chunks = chunk_documents([pf], max_chars=3000)
    assert len(chunks) == 1
    assert chunks[0].page_range == (1, 1)


def test_chunk_chapter_title_split():
    pf = _make_parsed(
        [
            ("第一章 概述\n\n这是第一节的内容", []),
            ("第二章 方法\n\n这是第二节的内容", []),
        ]
    )
    chunks = chunk_documents([pf], max_chars=3000)
    assert len(chunks) == 2


def test_chunk_cross_file_no_merge():
    pf1 = _make_parsed([("File A content", [])], "a.pdf")
    pf2 = _make_parsed([("File B content", [])], "b.pdf")
    chunks = chunk_documents([pf1, pf2], max_chars=3000)
    assert len(chunks) == 2
    assert chunks[0].source_file == "a.pdf"
    assert chunks[1].source_file == "b.pdf"


def test_chunk_has_tables_flag():
    pf = _make_parsed([("Page with table", ["| A | B |\n|---|---|\n| 1 | 2 |"])])
    chunks = chunk_documents([pf], max_chars=3000)
    assert chunks[0].has_tables is True
    assert len(chunks[0].tables_md) == 1


def test_chunk_no_tables_flag():
    pf = _make_parsed([("Page without table", [])])
    chunks = chunk_documents([pf], max_chars=3000)
    assert chunks[0].has_tables is False
    assert chunks[0].tables_md == []


def test_chunk_id_sequential():
    pf1 = _make_parsed([("A", []), ("B", []), ("C", [])], "f1.pdf")
    pf2 = _make_parsed([("D", []), ("E", [])], "f2.pdf")
    chunks = chunk_documents([pf1, pf2], max_chars=2)
    ids = [c.chunk_id for c in chunks]
    assert ids == ["chunk_001", "chunk_002", "chunk_003", "chunk_004", "chunk_005"]


def test_scan_folder(tmp_path):
    (tmp_path / "a.pdf").write_text("")
    (tmp_path / "b.pptx").write_text("")
    (tmp_path / "c.docx").write_text("")
    (tmp_path / "d.txt").write_text("")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "e.pdf").write_text("")
    result = scan_folder(str(tmp_path))
    assert len(result) == 2
    names = [os.path.basename(f) for f in result]
    assert "a.pdf" in names
    assert "b.pptx" in names


def test_scan_folder_empty(tmp_path):
    result = scan_folder(str(tmp_path))
    assert result == []
