import os
import tempfile
from sqlalchemy import create_engine, inspect
from crammer.db.store import init_db

EXPECTED_TABLES = {
    "subjects",
    "chapters",
    "knowledge_points",
    "cards",
    "calc_problems",
    "review_logs",
    "error_bookmarks",
    "daily_sessions",
}


def test_init_db_creates_all_tables():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        init_db(db_path)

        engine = create_engine(f"sqlite:///{db_path}")
        inspector = inspect(engine)
        actual_tables = set(inspector.get_table_names())
        engine.dispose()
        assert actual_tables == EXPECTED_TABLES, f"Missing: {EXPECTED_TABLES - actual_tables}, Extra: {actual_tables - EXPECTED_TABLES}"
    finally:
        os.unlink(db_path)
