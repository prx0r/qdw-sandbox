from pathlib import Path
import sqlite3
import pytest
from sandbox.core import Database

@pytest.fixture
def estate_db(tmp_path):
    db = Database(tmp_path / 'qdw.db')
    db.migrate()  # This already applies 0008_estate_core.sql
    return db
