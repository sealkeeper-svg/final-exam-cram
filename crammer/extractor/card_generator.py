import json
from crammer.utils import deepseek_chat
from crammer.config import get_api_key
from crammer.db.store import (
    get_knowledge_points, add_card, add_calc_problem,
    get_chapters, get_subject
)
from crammer.templates import find_template, get_all_templates

PROMPT_CONCEPT_CARDS = """你是一个大学期末考试出题助手。科目：{subject_name}。

根据以下知识点列表，为每个知识点生成 2-3 张不同类型的记忆卡片。

知识点列表：
{kps_text}

要求：
1. 每张卡片包含 card_type（definition/short_answer/discrimination）、question、answer、difficulty（基础/进阶）
2. 定义类：要求解释概念的核心含义
3. 简答类：要求列举要点或简述逻辑
4. 辨析类：正误判断 + 解释原因
5. 与科目内容紧密相关，使用课本术语

请严格按照以下 JSON 格式输出，不要输出其他内容：
{{"cards": [{{"kp_title": "知识点名称", "cards": [{{"card_type": "definition", "question": "...", "answer": "...", "difficulty": "基础"}}]}}]}}"""


def generate_cards_for_subject(subject_id, api_key=None, on_progress=None, db_path="data/crammer.db"):
    if api_key is None:
        api_key = get_api_key()

    subject = get_subject(subject_id, db_path=db_path)
    if not subject:
        raise ValueError(f"Subject {subject_id} not found")

    chapters = get_chapters(subject_id, db_path=db_path)
    active_chapters = [c for c in chapters if c.status == 'active']

    all_kps = []
    for ch in active_chapters:
        kps = get_knowledge_points(ch.id, db_path=db_path)
        all_kps.extend(kps)

    concept_kps = [kp for kp in all_kps if kp.type == 'concept']
    calc_kps = [kp for kp in all_kps if kp.type == 'calculation']

    concept_cards_count = 0
    calc_problems_count = 0
    calc_unmatched = 0
    registry = get_all_templates()

    batch_size = 10
    total_batches = (len(concept_kps) + batch_size - 1) // batch_size if concept_kps else 0

    for batch_idx in range(0, len(concept_kps), batch_size):
        batch = concept_kps[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        try:
            kps_text = "\n\n".join([f"- {kp.title}：{kp.content}" for kp in batch])
            prompt = PROMPT_CONCEPT_CARDS.format(
                subject_name=subject.name,
                kps_text=kps_text
            )
            messages = [{"role": "user", "content": prompt}]
            response = deepseek_chat(messages, api_key)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("\n", 1)[0]
            data = json.loads(response)

            for item in data.get("cards", []):
                kp_title = item.get("kp_title", "")
                kp = next((k for k in batch if k.title == kp_title), batch[0] if batch else None)
                if kp is None:
                    continue
                for card_data in item.get("cards", []):
                    add_card(
                        kp_id=kp.id,
                        card_type=card_data.get("card_type", "definition"),
                        question=card_data.get("question", ""),
                        answer=card_data.get("answer", ""),
                        difficulty=card_data.get("difficulty", "基础"),
                        db_path=db_path
                    )
                    concept_cards_count += 1

        except Exception:
            pass

        if on_progress:
            on_progress(batch_num, total_batches, batch[0].chunk_id if hasattr(batch[0], 'chunk_id') else "")

    for kp in calc_kps:
        template_name = None
        for tmpl in registry:
            if tmpl.subject in subject.name and any(
                kw in kp.title or kw in (kp.content or "")
                for kw in [tmpl.name]
            ):
                template_name = tmpl.name
                try:
                    problems = tmpl.generate_batch(5)
                    for prob in problems:
                        add_calc_problem(
                            kp_id=kp.id,
                            question_text=prob.question_text,
                            answer_text=prob.answer_text,
                            template_name=tmpl.name,
                            params_json=prob.params_json,
                            generated_by="template",
                            db_path=db_path
                        )
                        calc_problems_count += 1
                except Exception:
                    pass
                break

        if template_name is None:
            calc_unmatched += 1

    return {
        "concept_cards": concept_cards_count,
        "calc_problems": calc_problems_count,
        "calc_unmatched": calc_unmatched
    }


def get_template_registry():
    return get_all_templates()
