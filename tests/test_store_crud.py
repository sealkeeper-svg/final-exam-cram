import os
import tempfile
from datetime import date
from crammer.db.store import init_db, add_subject, get_subject


def test_add_and_get_subject_roundtrip():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        init_db(db_path)

        subject = add_subject(
            "高等数学",
            exam_date=date(2026, 6, 20),
            db_path=db_path,
        )

        assert subject.id is not None
        assert subject.name == "高等数学"
        assert subject.exam_date == date(2026, 6, 20)
        assert subject.archived is False

        fetched = get_subject(subject.id, db_path=db_path)
        assert fetched is not None
        assert fetched.id == subject.id
        assert fetched.name == "高等数学"
    finally:
        os.unlink(db_path)
