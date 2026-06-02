import pytest
from crammer.parser.pdf_parser import parse_pdf


def _make_pdf(filepath, text="Hello World"):
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content_stream = f"BT /F0 12 Tf 50 700 Td ({escaped}) Tj ET"
    content_bytes = content_stream.encode("ascii", errors="replace")

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n")

    offsets = {}

    def add_obj(num, raw):
        start = len(pdf)
        pdf.extend(f"{num} 0 obj\n".encode())
        if isinstance(raw, str):
            pdf.extend(raw.encode())
        else:
            pdf.extend(raw)
        pdf.extend(b"\nendobj\n")
        return start

    offsets[2] = add_obj(2, "<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    offsets[4] = add_obj(
        4,
        f"<< /Length {len(content_bytes)} >>\nstream\n".encode()
        + content_bytes
        + b"\nendstream",
    )
    offsets[5] = add_obj(5, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    offsets[3] = add_obj(
        3,
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Contents 4 0 R /Resources << /Font << /F0 5 0 R >> >> >>",
    )
    offsets[1] = add_obj(1, "<< /Type /Catalog /Pages 2 0 R >>")

    xref_start = len(pdf)
    pdf.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for i in range(1, 6):
        pdf.extend(f"{offsets[i]:010d} 00000 n \n".encode())

    pdf.extend(b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n")
    pdf.extend(f"{xref_start}\n".encode())
    pdf.extend(b"%%EOF\n")

    with open(filepath, "wb") as f:
        f.write(pdf)


def test_parse_pdf_single_page(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    _make_pdf(str(pdf_path), "Page One Content")

    result = parse_pdf(str(pdf_path))
    assert result["total_pages"] == 1
    assert "Page One Content" in result["pages"][0]["text"]
    assert result["pages"][0]["page_num"] == 1
    assert result["pages"][0]["tables"] == []


def test_parse_pdf_multi_page(tmp_path):
    pdf_path = tmp_path / "multi.pdf"
    _make_pdf(str(pdf_path), "First Page\n\nSecond Page Content")

    result = parse_pdf(str(pdf_path))
    assert result["total_pages"] >= 1


def test_parse_pdf_missing_file():
    result = parse_pdf("/nonexistent/file_12345.pdf")
    assert result["total_pages"] == 0
    assert result["pages"] == []
    assert "error" in result
