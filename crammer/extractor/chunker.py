import os
from dataclasses import dataclass, field


@dataclass
class Chunk:
    chunk_id: str
    text: str
    page_range: tuple
    source_file: str
    has_tables: bool
    tables_md: list = field(default_factory=list)


def chunk_documents(parsed_files, max_chars=3000):
    chunks = []
    chunk_idx = 0

    for pf in parsed_files:
        pages = pf.get("pages", [])
        source = pf.get("source_file", "unknown")

        current_page_nums = []
        current_text_parts = []
        current_tables = []

        for page in pages:
            page_text = page.get("text", "")
            page_tables = page.get("tables", [])
            page_num = page.get("page_num", 0)

            if _starts_with_chapter(page_text) and current_text_parts:
                chunk_idx += 1
                chunks.append(
                    Chunk(
                        chunk_id=f"chunk_{chunk_idx:03d}",
                        text="\n".join(current_text_parts),
                        page_range=(current_page_nums[0], current_page_nums[-1]),
                        source_file=source,
                        has_tables=bool(current_tables),
                        tables_md=list(current_tables),
                    )
                )
                current_page_nums = []
                current_text_parts = []
                current_tables = []

            test_parts = current_text_parts + [page_text]
            test_text = "\n".join(test_parts)

            if (
                len(test_text) > max_chars
                and current_text_parts
            ):
                chunk_idx += 1
                chunks.append(
                    Chunk(
                        chunk_id=f"chunk_{chunk_idx:03d}",
                        text="\n".join(current_text_parts),
                        page_range=(current_page_nums[0], current_page_nums[-1]),
                        source_file=source,
                        has_tables=bool(current_tables),
                        tables_md=list(current_tables),
                    )
                )
                current_page_nums = [page_num]
                current_text_parts = [page_text]
                current_tables = list(page_tables)
            else:
                current_page_nums.append(page_num)
                current_text_parts.append(page_text)
                current_tables.extend(page_tables)

        if current_text_parts and any(t.strip() for t in current_text_parts):
            chunk_idx += 1
            chunks.append(
                Chunk(
                    chunk_id=f"chunk_{chunk_idx:03d}",
                    text="\n".join(current_text_parts),
                    page_range=(current_page_nums[0], current_page_nums[-1]),
                    source_file=source,
                    has_tables=bool(current_tables),
                    tables_md=list(current_tables),
                )
            )

    return chunks


def _starts_with_chapter(text):
    first_line = ""
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            first_line = stripped
            break
    if not (5 <= len(first_line) <= 25):
        return False
    if not _is_all_chinese(first_line):
        return False
    return True


def _is_all_chinese(text):
    for ch in text:
        if "一" <= ch <= "鿿" or "㐀" <= ch <= "䶿":
            continue
        if ch in "·、，。；：？！""''（）《》【】…—":
            continue
        if ch.isspace():
            continue
        return False
    return True


def scan_folder(folder_path):
    result = []
    if not os.path.isdir(folder_path):
        return result
    for f in os.listdir(folder_path):
        full = os.path.join(folder_path, f)
        if not os.path.isfile(full):
            continue
        lower = f.lower()
        if lower.endswith(".pdf") or lower.endswith(".pptx"):
            result.append(full)
    return sorted(result)
