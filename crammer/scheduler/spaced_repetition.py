from datetime import date, timedelta


def next_review_date(result, current_interval, exam_date):
    if current_interval <= 0:
        new_interval = 1
    elif result == 'pass':
        new_interval = min(current_interval * 2, 16)
    else:
        new_interval = 1

    today = date.today()
    proposed = today + timedelta(days=new_interval)
    if proposed > exam_date:
        return exam_date
    return proposed


def get_due_cards(subject_id, limit=None, db_path="data/crammer.db"):
    from crammer.db.store import get_cards, get_knowledge_points, get_chapters
    chapters = get_chapters(subject_id, db_path=db_path)
    active = [c for c in chapters if c.status == 'active']
    today = date.today()

    due = []
    for ch in active:
        kps = get_knowledge_points(ch.id, db_path=db_path)
        for kp in kps:
            cards = get_cards(kp.id, db_path=db_path)
            for card in cards:
                if kp.next_review_at is None or kp.next_review_at.date() <= today:
                    due.append((card, kp))

    due.sort(key=lambda x: x[1].next_review_at or date(2000, 1, 1))

    if limit:
        return due[:limit]
    return due


def get_due_calc_problems(subject_id, limit=None, db_path="data/crammer.db"):
    from crammer.db.store import get_calc_problems, get_knowledge_points, get_chapters
    chapters = get_chapters(subject_id, db_path=db_path)
    active = [c for c in chapters if c.status == 'active']
    today = date.today()

    due = []
    for ch in active:
        kps = get_knowledge_points(ch.id, db_path=db_path)
        for kp in kps:
            problems = get_calc_problems(kp.id, db_path=db_path)
            for prob in problems:
                if kp.next_review_at is None or kp.next_review_at.date() <= today:
                    due.append((prob, kp))

    due.sort(key=lambda x: x[1].next_review_at or date(2000, 1, 1))

    if limit:
        return due[:limit]
    return due


def get_subject_dashboard(subject_id, db_path="data/crammer.db"):
    from crammer.db.store import get_subject, get_chapters, get_knowledge_points, get_cards
    import datetime

    subject = get_subject(subject_id, db_path=db_path)
    if not subject:
        return {}

    chapters = get_chapters(subject_id, db_path=db_path)
    active = [c for c in chapters if c.status == 'active']

    total_kps = 0
    mastered_kps = 0
    total_cards = 0
    reviewed_cards = 0

    today = date.today()
    due_today = 0

    for ch in active:
        kps = get_knowledge_points(ch.id, db_path=db_path)
        for kp in kps:
            total_kps += 1
            if kp.mastery >= 0.8:
                mastered_kps += 1
            cards = get_cards(kp.id, db_path=db_path)
            total_cards += len(cards)
            if kp.last_reviewed:
                reviewed_cards += len(cards)
            if kp.next_review_at is None or kp.next_review_at.date() <= today:
                due_today += len(cards)

    days_until_exam = (subject.exam_date - today).days if subject.exam_date else 0

    return {
        "total_kps": total_kps,
        "mastered_kps": mastered_kps,
        "mastery_pct": round(mastered_kps / total_kps * 100, 1) if total_kps else 0,
        "due_cards_today": due_today,
        "due_calc_today": 0,
        "days_until_exam": days_until_exam,
        "total_cards": total_cards,
        "reviewed_cards": reviewed_cards,
    }


def update_kp_after_review(kp_id, result, exam_date, time_spent=0, card_id=None, calc_problem_id=None, db_path="data/crammer.db"):
    from crammer.db.store import (
        add_review_log, upsert_error_bookmark, get_knowledge_points, get_chapters
    )
    from datetime import datetime
    from sqlalchemy import create_engine, update
    from sqlalchemy.orm import Session
    import crammer.db.models as m

    engine = create_engine(f"sqlite:///{db_path}")
    with Session(engine) as session:
        kp = session.query(m.KnowledgePoint).filter(m.KnowledgePoint.id == kp_id).first()
        if not kp:
            return

        if kp.last_reviewed and kp.next_review_at:
            current_interval = (kp.next_review_at - kp.last_reviewed).days
        else:
            current_interval = 0

        new_mastery = min(kp.mastery + 0.15, 1.0) if result == 'pass' else max(kp.mastery - 0.05, 0.0)
        error_count = kp.error_count + (0 if result == 'pass' else 1)
        next_date = next_review_date(result, current_interval, exam_date)

        session.execute(
            update(m.KnowledgePoint)
            .where(m.KnowledgePoint.id == kp_id)
            .values(
                mastery=new_mastery,
                error_count=error_count,
                last_reviewed=date.today(),
                next_review_at=next_date,
            )
        )
        session.commit()

    add_review_log(
        card_id=card_id,
        calc_problem_id=calc_problem_id,
        result=result,
        time_spent=time_spent,
        db_path=db_path
    )

    if result == 'fail':
        upsert_error_bookmark(
            card_id=card_id,
            calc_problem_id=calc_problem_id,
            db_path=db_path
        )
