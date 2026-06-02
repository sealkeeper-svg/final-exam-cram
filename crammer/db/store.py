from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from crammer.db.models import (
    Base,
    CalcProblem,
    Card,
    Chapter,
    DailySession,
    ErrorBookmark,
    KnowledgePoint,
    ReviewLog,
    Subject,
)


def _get_engine(db_path):
    return create_engine(f"sqlite:///{db_path}")


def init_db(db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    Base.metadata.create_all(engine)
    engine.dispose()


def add_subject(name, exam_date, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            subject = Subject(name=name, exam_date=exam_date)
            session.add(subject)
            session.commit()
            session.refresh(subject)
            return subject
    finally:
        engine.dispose()


def get_subject(subject_id, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            return session.get(Subject, subject_id)
    finally:
        engine.dispose()


def list_subjects(include_archived=False, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            stmt = select(Subject)
            if not include_archived:
                stmt = stmt.where(Subject.archived == False)
            return list(session.scalars(stmt))
    finally:
        engine.dispose()


def archive_subject(subject_id, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            subject = session.get(Subject, subject_id)
            if subject:
                subject.archived = True
                session.commit()
    finally:
        engine.dispose()


def add_chapter(subject_id, title, order, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            chapter = Chapter(subject_id=subject_id, title=title, order=order)
            session.add(chapter)
            session.commit()
            session.refresh(chapter)
            return chapter
    finally:
        engine.dispose()


def get_chapters(subject_id, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            stmt = (
                select(Chapter)
                .where(Chapter.subject_id == subject_id, Chapter.status == "active")
                .order_by(Chapter.order)
            )
            return list(session.scalars(stmt))
    finally:
        engine.dispose()


def delete_chapter(chapter_id, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            chapter = session.get(Chapter, chapter_id)
            if chapter:
                chapter.status = "deleted"
                session.commit()
    finally:
        engine.dispose()


def add_knowledge_point(chapter_id, title, content, type, formula=None, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            kp = KnowledgePoint(
                chapter_id=chapter_id,
                title=title,
                content=content,
                type=type,
                formula=formula,
            )
            session.add(kp)
            session.commit()
            session.refresh(kp)
            return kp
    finally:
        engine.dispose()


def get_knowledge_points(chapter_id, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            stmt = select(KnowledgePoint).where(KnowledgePoint.chapter_id == chapter_id)
            return list(session.scalars(stmt))
    finally:
        engine.dispose()


def add_card(kp_id, card_type, question, answer, difficulty="基础", db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            card = Card(
                kp_id=kp_id,
                card_type=card_type,
                question=question,
                answer=answer,
                difficulty=difficulty,
            )
            session.add(card)
            session.commit()
            session.refresh(card)
            return card
    finally:
        engine.dispose()


def get_cards(kp_id, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            stmt = select(Card).where(Card.kp_id == kp_id)
            return list(session.scalars(stmt))
    finally:
        engine.dispose()


def add_calc_problem(kp_id, question_text, answer_text, template_name=None, params_json=None, generated_by="template", db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            problem = CalcProblem(
                kp_id=kp_id,
                question_text=question_text,
                answer_text=answer_text,
                template_name=template_name,
                params_json=params_json,
                generated_by=generated_by,
            )
            session.add(problem)
            session.commit()
            session.refresh(problem)
            return problem
    finally:
        engine.dispose()


def get_calc_problems(kp_id, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            stmt = select(CalcProblem).where(CalcProblem.kp_id == kp_id)
            return list(session.scalars(stmt))
    finally:
        engine.dispose()


def add_review_log(card_id=None, calc_problem_id=None, result="pass", time_spent=0, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            log = ReviewLog(
                card_id=card_id,
                calc_problem_id=calc_problem_id,
                result=result,
                time_spent_seconds=time_spent,
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
    finally:
        engine.dispose()


def get_review_logs(subject_id=None, limit=50, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            stmt = select(ReviewLog)
            if subject_id is not None:
                stmt = (
                    stmt
                    .join(Card, ReviewLog.card_id == Card.id, isouter=True)
                    .join(CalcProblem, ReviewLog.calc_problem_id == CalcProblem.id, isouter=True)
                    .join(KnowledgePoint, (Card.kp_id == KnowledgePoint.id) | (CalcProblem.kp_id == KnowledgePoint.id), isouter=True)
                    .join(Chapter, KnowledgePoint.chapter_id == Chapter.id)
                    .where(Chapter.subject_id == subject_id)
                )
            stmt = stmt.order_by(ReviewLog.session_time.desc()).limit(limit)
            return list(session.scalars(stmt))
    finally:
        engine.dispose()


def upsert_error_bookmark(card_id=None, calc_problem_id=None, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            stmt = select(ErrorBookmark).where(
                ErrorBookmark.card_id == card_id,
                ErrorBookmark.calc_problem_id == calc_problem_id,
                ErrorBookmark.resolved == False,
            )
            existing = session.scalars(stmt).first()
            if existing:
                existing.error_count += 1
                session.commit()
                session.refresh(existing)
                return existing
            else:
                bookmark = ErrorBookmark(card_id=card_id, calc_problem_id=calc_problem_id)
                session.add(bookmark)
                session.commit()
                session.refresh(bookmark)
                return bookmark
    finally:
        engine.dispose()


def get_error_bookmarks(resolved=False, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            stmt = select(ErrorBookmark).where(ErrorBookmark.resolved == resolved)
            return list(session.scalars(stmt))
    finally:
        engine.dispose()


def resolve_error_bookmark(bookmark_id, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            bookmark = session.get(ErrorBookmark, bookmark_id)
            if bookmark:
                bookmark.resolved = True
                session.commit()
    finally:
        engine.dispose()


def upsert_daily_session(date, subject_id, cards_reviewed=0, accuracy=0.0, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            stmt = select(DailySession).where(
                DailySession.date == date,
                DailySession.subject_id == subject_id,
            )
            existing = session.scalars(stmt).first()
            if existing:
                existing.cards_reviewed += cards_reviewed
                if cards_reviewed > 0:
                    existing.accuracy = accuracy
                session.commit()
                session.refresh(existing)
                return existing
            else:
                session_obj = DailySession(
                    date=date,
                    subject_id=subject_id,
                    cards_reviewed=cards_reviewed,
                    accuracy=accuracy,
                )
                session.add(session_obj)
                session.commit()
                session.refresh(session_obj)
                return session_obj
    finally:
        engine.dispose()


def get_daily_sessions(subject_id, db_path="data/crammer.db"):
    engine = _get_engine(db_path)
    try:
        with Session(engine) as session:
            stmt = (
                select(DailySession)
                .where(DailySession.subject_id == subject_id)
                .order_by(DailySession.date.desc())
            )
            return list(session.scalars(stmt))
    finally:
        engine.dispose()
