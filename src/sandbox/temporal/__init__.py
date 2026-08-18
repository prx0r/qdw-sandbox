"""Temporal module — events, states, threads."""

from __future__ import annotations

import json
from typing import Any

from sandbox.core import Database
from sandbox.types import SpaceEvent, State, Thread, ThreadMember, ThreadStatus, new_id, utc_now


class EventStore:
    def __init__(self, db: Database):
        self.db = db

    def record_event(self, space_id: str, event_type_term_id: str, subject_entity_id: str,
                     object_entity_id: str = "", started_at: str = "", ended_at: str = "",
                     attributes: dict[str, Any] | None = None, confidence: float = 1.0) -> SpaceEvent:
        event = SpaceEvent(
            event_id=new_id("evt"),
            space_id=space_id,
            event_type_term_id=event_type_term_id,
            subject_entity_id=subject_entity_id,
            object_entity_id=object_entity_id,
            started_at=started_at or utc_now(),
            ended_at=ended_at,
            attributes=attributes or {},
            confidence=confidence,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO events
                   (event_id, space_id, event_type_term_id, subject_entity_id,
                    object_entity_id, started_at, ended_at, attributes_json,
                    confidence, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (event.event_id, event.space_id, event.event_type_term_id,
                 event.subject_entity_id, event.object_entity_id,
                 event.started_at, event.ended_at, json.dumps(event.attributes),
                 event.confidence, event.created_at),
            )
        return event

    def get_events_for(self, subject_entity_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            rows = con.execute(
                "SELECT * FROM events WHERE subject_entity_id = ? ORDER BY started_at",
                (subject_entity_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_events_in_space(self, space_id: str, event_type: str | None = None) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            if event_type:
                rows = con.execute(
                    "SELECT * FROM events WHERE space_id = ? AND event_type_term_id = ? ORDER BY started_at",
                    (space_id, event_type),
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT * FROM events WHERE space_id = ? ORDER BY started_at",
                    (space_id,),
                ).fetchall()
            return [dict(r) for r in rows]


class StateStore:
    def __init__(self, db: Database):
        self.db = db

    def set_state(self, space_id: str, subject_entity_id: str, dimension_term_id: str,
                  value: dict[str, Any], valid_from: str = "", confidence: float = 1.0) -> State:
        state = State(
            state_id=new_id("state"),
            space_id=space_id,
            subject_entity_id=subject_entity_id,
            dimension_term_id=dimension_term_id,
            value=value,
            valid_from=valid_from or utc_now(),
            confidence=confidence,
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO states
                   (state_id, space_id, subject_entity_id, dimension_term_id,
                    value_json, valid_from, valid_until, confidence, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (state.state_id, state.space_id, state.subject_entity_id,
                 state.dimension_term_id, json.dumps(state.value),
                 state.valid_from, state.valid_until, state.confidence, state.created_at),
            )
        return state

    def get_current_state(self, subject_entity_id: str, dimension_term_id: str) -> dict[str, Any] | None:
        with self.db.connect() as con:
            row = con.execute(
                """SELECT * FROM states
                   WHERE subject_entity_id = ? AND dimension_term_id = ?
                   AND (valid_until = '' OR valid_until > ?)
                   ORDER BY valid_from DESC LIMIT 1""",
                (subject_entity_id, dimension_term_id, utc_now()),
            ).fetchone()
            return dict(row) if row else None

    def get_all_states(self, subject_entity_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            rows = con.execute(
                "SELECT * FROM states WHERE subject_entity_id = ? ORDER BY valid_from",
                (subject_entity_id,),
            ).fetchall()
            return [dict(r) for r in rows]


class ThreadStore:
    def __init__(self, db: Database):
        self.db = db

    def create_thread(self, space_id: str, thread_type_term_id: str, primary_subject_id: str,
                      started_at: str = "") -> Thread:
        thread = Thread(
            thread_id=new_id("thread"),
            space_id=space_id,
            thread_type_term_id=thread_type_term_id,
            primary_subject_id=primary_subject_id,
            started_at=started_at or utc_now(),
        )
        with self.db.tx() as con:
            con.execute(
                """INSERT INTO threads
                   (thread_id, space_id, thread_type_term_id, primary_subject_id,
                    started_at, ended_at, status, confidence, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (thread.thread_id, thread.space_id, thread.thread_type_term_id,
                 thread.primary_subject_id, thread.started_at, thread.ended_at,
                 thread.status.value, thread.confidence, thread.created_at),
            )
        return thread

    def add_member(self, thread_id: str, member_type: str, member_id: str,
                   role_term_id: str = "", ordinal: int = 0) -> ThreadMember:
        member = ThreadMember(thread_id=thread_id, member_type=member_type,
                              member_id=member_id, role_term_id=role_term_id, ordinal=ordinal)
        with self.db.tx() as con:
            con.execute(
                """INSERT OR REPLACE INTO thread_members
                   (thread_id, member_type, member_id, role_term_id, ordinal)
                   VALUES (?, ?, ?, ?, ?)""",
                (member.thread_id, member.member_type, member.member_id,
                 member.role_term_id, member.ordinal),
            )
        return member

    def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        with self.db.connect() as con:
            row = con.execute("SELECT * FROM threads WHERE thread_id = ?", (thread_id,)).fetchone()
            return dict(row) if row else None

    def get_members(self, thread_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            rows = con.execute(
                "SELECT * FROM thread_members WHERE thread_id = ? ORDER BY ordinal",
                (thread_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_threads_for(self, subject_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as con:
            rows = con.execute(
                "SELECT * FROM threads WHERE primary_subject_id = ? ORDER BY started_at",
                (subject_id,),
            ).fetchall()
            return [dict(r) for r in rows]
