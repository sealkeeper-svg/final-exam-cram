import json
import re

from crammer.config import get_api_key
from crammer.db.store import add_chapter, add_knowledge_point, delete_chapter
from crammer.utils import deepseek_chat


def _build_system_prompt(subject_name):
    return (
        f"你是一个大学课程助教，正在为《{subject_name}》课程整理知识树。\n"
        "你会收到课件的部分文本片段，请从中提取结构化的知识树。\n\n"
        "输出要求：\n"
        "1. 按章节目录组织\n"
        "2. 每个知识点分为概念类（concept）和计算类（calculation）\n"
        "3. 概念类知识点必须包含 content（完整解释，不少于50字）\n"
        "4. 计算类知识点必须包含 formula（公式）和 content（公式说明）\n"
        "5. 只输出 JSON，不要输出任何其他文字\n\n"
        "JSON 格式：\n"
        '{"chapters": [{"title": "章标题", "order": 1, "sections": ['
        '{"title": "节标题", "knowledge_points": ['
        '{"name": "知识点名称", "type": "concept|calculation", "content": "内容", "formula": null|"公式"}]}]}]}'
    )


def _build_user_prompt(chunks, subject_name):
    texts = []
    for i, chunk in enumerate(chunks, 1):
        header = f"【片段{i}】来源：{chunk.source_file}，页码范围：{chunk.page_range[0]}-{chunk.page_range[1]}"
        texts.append(header)
        texts.append(chunk.text)
        if chunk.tables_md:
            texts.append("表格内容：")
            for table in chunk.tables_md:
                texts.append(table)
        texts.append("")
    joined = "\n".join(texts)
    return (
        f"以下是《{subject_name}》课件的文本片段，请提取知识树：\n\n{joined}"
    )


def _parse_json_response(response_text):
    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if json_match:
        return json.loads(json_match.group(0))
    return json.loads(response_text)


def _store_chapter(chapter_data, subject_id, db_path):
    chapter_row = add_chapter(subject_id, chapter_data["title"], chapter_data["order"], db_path=db_path)
    chapter_data["_chapter_id"] = chapter_row.id
    for section in chapter_data.get("sections", []):
        for kp in section.get("knowledge_points", []):
            add_knowledge_point(
                chapter_row.id,
                kp["name"],
                kp.get("content", ""),
                kp.get("type", "concept"),
                formula=kp.get("formula"),
                db_path=db_path,
            )


def _merge_batch_tree(batch_tree, all_chapters, result_tree, subject_id, db_path):
    existing_titles = {c["title"] for c in result_tree["chapters"]}
    for chapter_data in batch_tree.get("chapters", []):
        title = chapter_data["title"]
        if title in existing_titles:
            existing = next(c for c in result_tree["chapters"] if c["title"] == title)
            chapter_id = existing["_chapter_id"]
            for section in chapter_data.get("sections", []):
                existing_section = next(
                    (s for s in existing["sections"] if s["title"] == section["title"]), None
                )
                if existing_section:
                    existing_section["knowledge_points"].extend(section.get("knowledge_points", []))
                else:
                    existing["sections"].append(section)
                for kp in section.get("knowledge_points", []):
                    add_knowledge_point(
                        chapter_id,
                        kp["name"],
                        kp.get("content", ""),
                        kp.get("type", "concept"),
                        formula=kp.get("formula"),
                        db_path=db_path,
                    )
        else:
            _store_chapter(chapter_data, subject_id, db_path)
            result_tree["chapters"].append(chapter_data)
            existing_titles.add(title)


def build_knowledge_tree(chunks, subject_name, subject_id, api_key=None, on_progress=None, db_path="data/crammer.db"):
    if api_key is None:
        api_key = get_api_key()

    batch_size = 5
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    system_prompt = _build_system_prompt(subject_name)

    result_tree = {"chapters": [], "_db_path": db_path}

    for batch_idx in range(0, len(chunks), batch_size):
        batch = chunks[batch_idx:batch_idx + batch_size]
        current = batch_idx // batch_size + 1

        if on_progress:
            on_progress(current, total_batches, batch[0].chunk_id)

        try:
            user_prompt = _build_user_prompt(batch, subject_name)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response_text = deepseek_chat(messages, api_key)
            batch_tree = _parse_json_response(response_text)
            _merge_batch_tree(batch_tree, {}, result_tree, subject_id, db_path)
        except Exception:
            continue

    return result_tree


def confirm_chapters(tree, selected_indices, db_path=None):
    if db_path is None:
        db_path = tree.get("_db_path", "data/crammer.db")

    selected_set = set(selected_indices)
    result = {"chapters": [], "_db_path": db_path}

    for idx, chapter in enumerate(tree.get("chapters", [])):
        if idx in selected_set:
            result["chapters"].append(chapter)
        else:
            chapter_id = chapter.get("_chapter_id")
            if chapter_id is not None:
                delete_chapter(chapter_id, db_path=db_path)

    return result


def extract_metadata(tree):
    chapter_count = 0
    kp_count = 0
    concept_count = 0
    calculation_count = 0

    for chapter in tree.get("chapters", []):
        chapter_count += 1
        for section in chapter.get("sections", []):
            for kp in section.get("knowledge_points", []):
                kp_count += 1
                if kp.get("type") == "concept":
                    concept_count += 1
                elif kp.get("type") == "calculation":
                    calculation_count += 1

    return {
        "chapter_count": chapter_count,
        "kp_count": kp_count,
        "concept_count": concept_count,
        "calculation_count": calculation_count,
    }
