from dataclasses import dataclass, field
from crammer.db.store import get_subject, get_chapters, get_knowledge_points, get_cards


@dataclass
class LearningStep:
    step_num: int
    title: str
    explanation: str
    check_question: str
    check_answer: str
    insight: str
    kp_id: int

@dataclass
class LearningPath:
    path_id: str
    title: str
    description: str
    steps: list


def build_learning_paths(subject_id, db_path="data/crammer.db"):
    chapters = get_chapters(subject_id, db_path=db_path)
    active = [c for c in chapters if c.status == 'active']

    has_any_cards = False
    for ch in active:
        cards = get_cards(ch.id, db_path=db_path)
        if cards:
            has_any_cards = True
            break

    if not has_any_cards:
        return []

    paths = []
    step_size = 2
    all_steps = []

    for ch in active:
        kps = get_knowledge_points(ch.id, db_path=db_path)
        cards = get_cards(ch.id, db_path=db_path)

        kp_content = "\n\n".join([kp.content or "" for kp in kps if kp.content])
        check_q = cards[0].question if cards else ""
        check_a = cards[0].answer if cards else ""
        insight_text = ""
        if kps and kps[0].content:
            sentences = kps[0].content.replace("。", ".").split(".")
            insight_text = sentences[-1].strip() if sentences else ""
        kp_id = kps[0].id if kps else 0

        all_steps.append(LearningStep(
            step_num=0,
            title=ch.title,
            explanation=kp_content or ch.title,
            check_question=check_q,
            check_answer=check_a,
            insight=insight_text or "本章是后续内容的基础",
            kp_id=kp_id
        ))

    for i in range(0, len(all_steps), step_size):
        batch = all_steps[i:i + step_size]
        for j, step in enumerate(batch):
            step.step_num = j + 1

        path_title = batch[0].title
        if len(batch) > 1:
            path_title = f"{batch[0].title} → {batch[-1].title}"

        paths.append(LearningPath(
            path_id=f"path_{i // step_size:03d}",
            title=path_title,
            description=f"涵盖 {len(batch)} 个章节，{sum(1 for s in batch) * 2} 个知识点",
            steps=batch
        ))

    if len(all_steps) % step_size == 1 and len(paths) > 1:
        leftover = paths[-1].steps
        paths = paths[:-1]
        if paths:
            paths[-1].steps.extend(leftover)
            for j, step in enumerate(paths[-1].steps):
                step.step_num = j + 1

    return paths


def get_path_by_id(subject_id, path_id, db_path="data/crammer.db"):
    paths = build_learning_paths(subject_id, db_path=db_path)
    for p in paths:
        if p.path_id == path_id:
            return p
    return None


def format_step_for_display(step):
    lines = [
        f"━━━ {step.title} ━━━",
        "",
        step.explanation,
        "",
        f"📝 理解检查：{step.check_question}",
        "",
        f"💡 关键洞察：{step.insight}",
    ]
    return "\n".join(lines)
