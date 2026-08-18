"""SQLite database with versioned migrations for qdw-sandbox."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.db_path, timeout=10)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=5000")
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    @contextmanager
    def tx(self):
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            yield con

    def migrate(self):
        migrations_dir = Path(__file__).parent.parent.parent.parent / "migrations"
        with self.connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
            """)
            applied = {
                row["version"]
                for row in con.execute("SELECT version FROM schema_versions").fetchall()
            }

        if not migrations_dir.exists():
            return

        for path in sorted(migrations_dir.glob("*.sql")):
            parts = path.stem.split("_", 1)
            if len(parts) < 2:
                continue
            try:
                version = int(parts[0])
            except ValueError:
                continue
            if version in applied:
                continue
            sql = path.read_text()
            with self.tx() as con:
                con.executescript(sql)
                con.execute(
                    "INSERT INTO schema_versions (version, name, applied_at) VALUES (?, ?, ?)",
                    (version, path.stem, __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()),
                )
