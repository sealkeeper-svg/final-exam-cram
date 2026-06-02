from crammer.scheduler.spaced_repetition import (
    get_due_cards, get_due_calc_problems, get_subject_dashboard,
    update_kp_after_review
)
from crammer.db.store import get_subject


def start_daily_review(subject_id, db_path="data/crammer.db"):
    subject = get_subject(subject_id, db_path=db_path)
    if not subject:
        raise ValueError(f"Subject {subject_id} not found")

    dashboard = get_subject_dashboard(subject_id, db_path=db_path)
    cards = get_due_cards(subject_id, db_path=db_path)
    calc_problems = get_due_calc_problems(subject_id, db_path=db_path)

    return {
        "subject_name": subject.name,
        "dashboard": dashboard,
        "cards": cards,
        "calc_problems": calc_problems,
        "total_due": len(cards) + len(calc_problems),
    }


def record_review_result(
    card_id=None,
    calc_problem_id=None,
    kp_id=None,
    result="pass",
    exam_date=None,
    time_spent=0,
    db_path="data/crammer.db"
):
    if kp_id is None:
        raise ValueError("kp_id is required")
    if exam_date is None:
        raise ValueError("exam_date is required")

    update_kp_after_review(
        kp_id=kp_id,
        result=result,
        exam_date=exam_date,
        time_spent=time_spent,
        card_id=card_id,
        calc_problem_id=calc_problem_id,
        db_path=db_path
    )
    return {"status": "ok", "result": result}
