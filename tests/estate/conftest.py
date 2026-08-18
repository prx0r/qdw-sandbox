from pathlib import Path
import sqlite3
import pytest
from sandbox.core import Database

@pytest.fixture
def estate_db(tmp_path):
    db = Database(tmp_path / 'qdw.db')
    db.migrate()
    # Apply Estate migration explicitly
    sql = Path(__file__).parents[2] / 'migrations' / '0008_estate_core.sql'
    if not sql.exists():
        sql = Path('migrations/0008_estate_core.sql')
    with db.connect() as c:
        c.executescript(sql.read_text())
    return db
