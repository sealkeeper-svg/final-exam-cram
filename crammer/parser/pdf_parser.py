import pdfplumber


def parse_pdf(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                raw_tables = page.extract_tables() or []
                md_tables = [_table_to_md(t) for t in raw_tables if t]
                pages.append(
                    {
                        "page_num": page.page_number,
                        "text": text,
                        "tables": md_tables,
                    }
                )
            return {"pages": pages, "total_pages": len(pages)}
    except Exception as e:
        return {"pages": [], "total_pages": 0, "error": str(e)}


def _table_to_md(table):
    if not table:
        return ""
    cleaned = [[str(c) if c is not None else "" for c in row] for row in table]
    col_count = max(len(row) for row in cleaned) if cleaned else 0
    rows = []
    for i, row in enumerate(cleaned):
        padded = row + [""] * (col_count - len(row))
        rows.append("| " + " | ".join(padded) + " |")
        if i == 0:
            rows.append("|" + "|".join(["---"] * col_count) + "|")
    return "\n".join(rows)
