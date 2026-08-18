from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from sandbox.lifegit.models import NormalizedConversation
from sandbox.lifegit.util import canonical_json, stable_id

SCHEMA="""
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS source_artifacts(
 artifact_id TEXT PRIMARY KEY, provider TEXT NOT NULL, source_path TEXT NOT NULL,
 member_name TEXT, sha256 TEXT NOT NULL UNIQUE, imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS spaces(
 space_id TEXT PRIMARY KEY, kind TEXT NOT NULL, label TEXT NOT NULL, visibility TEXT NOT NULL DEFAULT 'PRIVATE'
);
CREATE TABLE IF NOT EXISTS conversations(
 conversation_id TEXT PRIMARY KEY, provider TEXT NOT NULL, artifact_id TEXT NOT NULL,
 title TEXT NOT NULL, created_at TEXT, updated_at TEXT, metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_conversations_time ON conversations(created_at);
CREATE TABLE IF NOT EXISTS messages(
 message_id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, provider TEXT NOT NULL,
 parent_message_id TEXT, role TEXT NOT NULL, text TEXT NOT NULL, created_at TEXT,
 model TEXT, is_current_path INTEGER NOT NULL DEFAULT 1, metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(created_at);
CREATE TABLE IF NOT EXISTS semantic_objects(
 object_id TEXT PRIMARY KEY, space_id TEXT NOT NULL, object_type TEXT NOT NULL,
 canonical_text TEXT NOT NULL, normalized_key TEXT NOT NULL, first_observed_at TEXT,
 last_observed_at TEXT, status TEXT NOT NULL DEFAULT 'ACTIVE', confidence REAL NOT NULL,
 extractor_version TEXT NOT NULL, privacy_class TEXT NOT NULL DEFAULT 'PRIVATE', work_relevance REAL NOT NULL DEFAULT 0,
 evidence_message_id TEXT NOT NULL, evidence_conversation_id TEXT NOT NULL, attributes_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_semantic_type ON semantic_objects(object_type, first_observed_at);
CREATE INDEX IF NOT EXISTS idx_semantic_key ON semantic_objects(object_type, normalized_key);
CREATE TABLE IF NOT EXISTS object_links(
 link_id TEXT PRIMARY KEY, subject_object_id TEXT NOT NULL, predicate TEXT NOT NULL,
 object_object_id TEXT NOT NULL, confidence REAL NOT NULL, attributes_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS events(
 event_id TEXT PRIMARY KEY, space_id TEXT NOT NULL, event_type TEXT NOT NULL,
 subject_object_id TEXT, occurred_at TEXT, confidence REAL NOT NULL,
 evidence_message_id TEXT NOT NULL, attributes_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS tensions(
 tension_id TEXT PRIMARY KEY, space_id TEXT NOT NULL, tension_type TEXT NOT NULL,
 current_state TEXT NOT NULL, desired_state TEXT, recurrence REAL NOT NULL DEFAULT 0,
 intensity REAL NOT NULL DEFAULT 0, confidence REAL NOT NULL DEFAULT 0,
 first_observed_at TEXT, last_observed_at TEXT, evidence_count INTEGER NOT NULL DEFAULT 0,
 attributes_json TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS report_runs(
 report_run_id TEXT PRIMARY KEY, report_type TEXT NOT NULL, space_id TEXT NOT NULL,
 period_start TEXT, period_end TEXT, output_path TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

class LifeDB:
    def __init__(self,path: str|Path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as con:
            con.executescript(SCHEMA)
            con.execute("INSERT OR IGNORE INTO spaces(space_id,kind,label,visibility) VALUES('life:default','PERSONAL','Personal Life','PRIVATE')")

    @contextmanager
    def connect(self):
        con=sqlite3.connect(self.path)
        con.row_factory=sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def import_conversations(self, conversations: list[NormalizedConversation], *, artifact_sha: str, provider: str, source_path: str, member_name: str) -> dict:
        artifact_id=stable_id("artifact",provider,artifact_sha)
        added_convs=added_msgs=0
        with self.connect() as con:
            con.execute("INSERT OR IGNORE INTO source_artifacts(artifact_id,provider,source_path,member_name,sha256) VALUES(?,?,?,?,?)",
                        (artifact_id,provider,source_path,member_name,artifact_sha))
            for c in conversations:
                before=con.total_changes
                con.execute("INSERT OR IGNORE INTO conversations(conversation_id,provider,artifact_id,title,created_at,updated_at,metadata_json) VALUES(?,?,?,?,?,?,?)",
                            (c.conversation_id,c.provider,artifact_id,c.title,c.created_at,c.updated_at,canonical_json(c.metadata)))
                if con.total_changes>before: added_convs+=1
                for m in c.messages:
                    before=con.total_changes
                    con.execute("INSERT OR IGNORE INTO messages(message_id,conversation_id,provider,parent_message_id,role,text,created_at,model,is_current_path,metadata_json) VALUES(?,?,?,?,?,?,?,?,?,?)",
                                (m.message_id,m.conversation_id,m.provider,m.parent_message_id,m.role,m.text,m.created_at,m.model,int(m.is_current_path),canonical_json(m.metadata)))
                    if con.total_changes>before: added_msgs+=1
        return {"artifact_id":artifact_id,"conversations_added":added_convs,"messages_added":added_msgs}

    def stats(self) -> dict:
        with self.connect() as con:
            return {k: con.execute(f"SELECT COUNT(*) n FROM {k}").fetchone()["n"] for k in ["source_artifacts","conversations","messages","semantic_objects","events","tensions"]}
