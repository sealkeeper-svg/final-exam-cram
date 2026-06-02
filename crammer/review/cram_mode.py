from crammer.db.store import get_subject, get_chapters, get_knowledge_points, get_cards, get_calc_problems, get_error_bookmarks


def get_cram_flash_cards(subject_id, db_path="data/crammer.db"):
    chapters = get_chapters(subject_id, db_path=db_path)
    active = [c for c in chapters if c.status == 'active']
    cards = []

    for ch in active:
        kps = get_knowledge_points(ch.id, db_path=db_path)
        for kp in kps:
            concept_cards = get_cards(kp.id, db_path=db_path)
            for card in concept_cards:
                cards.append({
                    "type": "概念", "question": card.question,
                    "answer": card.answer, "mastery": kp.mastery
                })
            calc_probs = get_calc_problems(kp.id, db_path=db_path)
            for prob in calc_probs:
                cards.append({
                    "type": "计算", "question": prob.question_text,
                    "answer": prob.answer_text, "mastery": kp.mastery
                })

    cards.sort(key=lambda x: x["mastery"])
    return cards


def get_key_points(subject_id, db_path="data/crammer.db"):
    chapters = get_chapters(subject_id, db_path=db_path)
    active = [c for c in chapters if c.status == 'active']
    formulas = []
    core_concepts = []
    high_error_kps = []

    for ch in active:
        kps = get_knowledge_points(ch.id, db_path=db_path)
        for kp in kps:
            if kp.formula:
                formulas.append(kp.formula)
            if kp.difficulty == '进阶':
                core_concepts.append({"name": kp.title, "content": kp.content or ""})
            if kp.error_count > 0:
                high_error_kps.append({"name": kp.title, "error_count": kp.error_count})

    high_error_kps.sort(key=lambda x: x["error_count"], reverse=True)
    high_error_kps = high_error_kps[:10]

    return {
        "formulas": formulas,
        "core_concepts": core_concepts,
        "high_error_kps": high_error_kps,
    }


def get_error_redo_cards(subject_id, db_path="data/crammer.db"):
    bookmarks = get_error_bookmarks(resolved=False, db_path=db_path)
    result = []

    for bm in bookmarks:
        if bm.card_id:
            from sqlalchemy.orm import Session
            from sqlalchemy import create_engine, select
            import crammer.db.models as m

            engine = create_engine(f"sqlite:///{db_path}")
            with Session(engine) as session:
                card = session.get(m.Card, bm.card_id)
                if card:
                    kp = session.get(m.KnowledgePoint, card.kp_id)
                    if kp:
                        ch = session.get(m.Chapter, kp.chapter_id)
                        if ch and ch.subject_id == subject_id:
                            result.append({
                                "question": card.question,
                                "answer": card.answer,
                                "error_count": bm.error_count,
                            })
            engine.dispose()

    return result
