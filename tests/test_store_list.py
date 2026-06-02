import os
import tempfile
from datetime import date
from crammer.db.store import init_db, add_subject, list_subjects, archive_subject


def test_list_subjects_and_archive_filter():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        init_db(db_path)

        add_subject("数学", exam_date=date(2026, 6, 15), db_path=db_path)
        add_subject("物理", exam_date=date(2026, 6, 18), db_path=db_path)
        add_subject("英语", exam_date=date(2026, 6, 22), db_path=db_path)

        all_subjects = list_subjects(include_archived=False, db_path=db_path)
        assert len(all_subjects) == 3
        assert {s.name for s in all_subjects} == {"数学", "物理", "英语"}

        archive_subject(all_subjects[0].id, db_path=db_path)

        active = list_subjects(include_archived=False, db_path=db_path)
        assert len(active) == 2

        all_including = list_subjects(include_archived=True, db_path=db_path)
        assert len(all_including) == 3
        assert any(s.archived for s in all_including)
    finally:
        os.unlink(db_path)
