import random
from crammer.db.store import get_subject, get_chapters, get_knowledge_points, get_cards, get_calc_problems
from crammer.review.daily_review import record_review_result


def generate_quiz(subject_id, num_questions=15, db_path="data/crammer.db"):
    subject = get_subject(subject_id, db_path=db_path)
    chapters = get_chapters(subject_id, db_path=db_path)
    active = [c for c in chapters if c.status == 'active']

    concept_pool = []
    calc_pool = []

    for ch in active:
        kps = get_knowledge_points(ch.id, db_path=db_path)
        for kp in kps:
            if kp.type == 'concept':
                cards = get_cards(kp.id, db_path=db_path)
                for card in cards:
                    concept_pool.append({
                        "type": "概念", "question": card.question, "answer": card.answer,
                        "card_id": card.id, "mastery": kp.mastery
                    })
            else:
                probs = get_calc_problems(kp.id, db_path=db_path)
                for prob in probs:
                    calc_pool.append({
                        "type": "计算", "question": prob.question_text, "answer": prob.answer_text,
                        "calc_problem_id": prob.id, "mastery": kp.mastery
                    })

    target_concept = int(num_questions * 0.7)
    target_calc = num_questions - target_concept

    selected_concept = random.sample(concept_pool, min(target_concept, len(concept_pool)))
    selected_calc = random.sample(calc_pool, min(target_calc, len(calc_pool)))

    if len(selected_concept) + len(selected_calc) < num_questions:
        remaining = num_questions - len(selected_concept) - len(selected_calc)
        leftover = [q for q in (concept_pool + calc_pool)
                    if q not in selected_concept and q not in selected_calc]
        if leftover:
            extra = random.sample(leftover, min(remaining, len(leftover)))
            selected_concept.extend([q for q in extra if q['type'] == '概念'])
            selected_calc.extend([q for q in extra if q['type'] == '计算'])

    questions = selected_concept + selected_calc
    random.shuffle(questions)
    questions = questions[:num_questions]

    return {
        "subject_name": subject.name,
        "questions": questions,
        "total": len(questions),
        "time_limit_minutes": 20,
    }


def score_quiz(questions, user_results, subject_id, db_path="data/crammer.db"):
    correct_count = 0
    wrong = []
    total_time = 0
    subject = get_subject(subject_id, db_path=db_path)
    exam_date = subject.exam_date if subject else None

    for q, ur in zip(questions, user_results):
        total_time += ur.get("time_spent", 0)
        is_correct = ur.get("correct", False)
        if is_correct:
            correct_count += 1
        else:
            wrong.append({"question": q["question"], "answer": q["answer"]})
            from crammer.db.store import get_knowledge_points
            if q.get("card_id"):
                kp_id = ur.get("kp_id")
                if kp_id and exam_date:
                    record_review_result(
                        card_id=q["card_id"], kp_id=kp_id,
                        result="fail", exam_date=exam_date,
                        db_path=db_path
                    )

    return {
        "score": correct_count,
        "total": len(questions),
        "accuracy": round(correct_count / len(questions) * 100, 1) if questions else 0,
        "wrong_questions": wrong,
        "time_total_seconds": total_time,
    }
