from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    exam_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    archived = Column(Boolean, default=False)

    chapters = relationship("Chapter", back_populates="subject", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    title = Column(String)
    order = Column(Integer)
    status = Column(String, default="active")

    subject = relationship("Subject", back_populates="chapters")
    knowledge_points = relationship("KnowledgePoint", back_populates="chapter", cascade="all, delete-orphan")


class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    title = Column(String)
    content = Column(Text)
    type = Column(String)
    formula = Column(Text, nullable=True)
    difficulty = Column(String, default="基础")
    mastery = Column(Float, default=0.0)
    error_count = Column(Integer, default=0)
    last_reviewed = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)

    chapter = relationship("Chapter", back_populates="knowledge_points")
    cards = relationship("Card", back_populates="knowledge_point", cascade="all, delete-orphan")
    calc_problems = relationship("CalcProblem", back_populates="knowledge_point", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True)
    kp_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False)
    card_type = Column(String)
    question = Column(Text)
    answer = Column(Text)
    difficulty = Column(String, default="基础")

    knowledge_point = relationship("KnowledgePoint", back_populates="cards")
    review_logs = relationship("ReviewLog", back_populates="card", cascade="all, delete-orphan")
    error_bookmarks = relationship("ErrorBookmark", back_populates="card", cascade="all, delete-orphan")


class CalcProblem(Base):
    __tablename__ = "calc_problems"

    id = Column(Integer, primary_key=True)
    kp_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False)
    template_name = Column(String, nullable=True)
    question_text = Column(Text)
    answer_text = Column(Text)
    params_json = Column(Text, nullable=True)
    generated_by = Column(String, default="template")
    generated_at = Column(DateTime, default=datetime.now)

    knowledge_point = relationship("KnowledgePoint", back_populates="calc_problems")
    review_logs = relationship("ReviewLog", back_populates="calc_problem", cascade="all, delete-orphan")
    error_bookmarks = relationship("ErrorBookmark", back_populates="calc_problem", cascade="all, delete-orphan")


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)
    calc_problem_id = Column(Integer, ForeignKey("calc_problems.id"), nullable=True)
    session_time = Column(DateTime, default=datetime.now)
    result = Column(String)
    time_spent_seconds = Column(Integer, default=0)

    card = relationship("Card", back_populates="review_logs")
    calc_problem = relationship("CalcProblem", back_populates="review_logs")


class ErrorBookmark(Base):
    __tablename__ = "error_bookmarks"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)
    calc_problem_id = Column(Integer, ForeignKey("calc_problems.id"), nullable=True)
    first_error_at = Column(DateTime, default=datetime.now)
    error_count = Column(Integer, default=1)
    resolved = Column(Boolean, default=False)

    card = relationship("Card", back_populates="error_bookmarks")
    calc_problem = relationship("CalcProblem", back_populates="error_bookmarks")


class DailySession(Base):
    __tablename__ = "daily_sessions"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    cards_reviewed = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
