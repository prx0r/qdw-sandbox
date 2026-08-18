"""Personal module — LifeGit infrastructure: ingest, extract, resolve, privacy, reports."""

from __future__ import annotations

import json
from typing import Any

from sandbox.core import Database
from sandbox.types import SemanticObjectType, new_id, utc_now


class PersonalIngestor:
    """Ingest personal data sources into private spaces."""

    def __init__(self, db: Database):
        self.db = db

    def ingest_chatgpt_export(self, space_id: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Ingest ChatGPT conversation export."""
        from sandbox.semantic import SemanticObjectStore
        store = SemanticObjectStore(self.db)
        count = 0
        for msg in messages:
            content = msg.get("content", "")
            role = msg.get("role", "unknown")
            if not content:
                continue
            key = f"chatgpt:{hash(content[:200])}"
            existing = store.find_by_key(space_id, key)
            if existing:
                store.touch(existing["object_id"])
            else:
                store.create_object(
                    space_id=space_id,
                    object_type=SemanticObjectType.IDEA if len(content) > 50 else SemanticObjectType.DISCOVERY,
                    canonical_key=key,
                    content={"role": role, "snippet": content[:500], "source": "chatgpt"},
                    confidence=0.8,
                )
                count += 1
        return {"ingested": count, "total": len(messages)}

    def ingest_generic_events(self, space_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
        """Ingest generic event records."""
        from sandbox.temporal import EventStore
        store = EventStore(self.db)
        count = 0
        for evt in events:
            store.record_event(
                space_id=space_id,
                event_type_term_id=evt.get("type", "discovery"),
                subject_entity_id=evt.get("subject", ""),
                attributes=evt.get("attributes", {}),
            )
            count += 1
        return {"ingested": count}


class PersonalExtractor:
    """Extract structured objects from personal data."""

    def __init__(self, db: Database):
        self.db = db

    def extract_questions(self, space_id: str) -> list[dict[str, Any]]:
        from sandbox.semantic import SemanticObjectStore
        store = SemanticObjectStore(self.db)
        return store.list_objects(space_id=space_id, object_type="question")

    def extract_ideas(self, space_id: str) -> list[dict[str, Any]]:
        from sandbox.semantic import SemanticObjectStore
        store = SemanticObjectStore(self.db)
        return store.list_objects(space_id=space_id, object_type="idea")

    def extract_goals(self, space_id: str) -> list[dict[str, Any]]:
        from sandbox.semantic import SemanticObjectStore
        store = SemanticObjectStore(self.db)
        return store.list_objects(space_id=space_id, object_type="goal")


class PersonalTimeline:
    """Project temporal timeline from events and states."""

    def __init__(self, db: Database):
        self.db = db

    def get_timeline(self, space_id: str, subject_id: str) -> dict[str, Any]:
        from sandbox.temporal import EventStore, StateStore
        events = EventStore(self.db).get_events_for(subject_id)
        states = StateStore(self.db).get_all_states(subject_id)
        return {
            "subject_id": subject_id,
            "events": events,
            "states": states,
            "event_count": len(events),
            "state_count": len(states),
        }


class PersonalPrivacy:
    """Manage space visibility and grants."""

    def __init__(self, db: Database):
        self.db = db

    def set_visibility(self, space_id: str, visibility: str) -> None:
        with self.db.tx() as con:
            con.execute("UPDATE spaces SET default_visibility = ? WHERE space_id = ?", (visibility, space_id))

    def check_access(self, space_id: str, grantee_id: str) -> bool:
        with self.db.connect() as con:
            row = con.execute(
                "SELECT default_visibility FROM spaces WHERE space_id = ?", (space_id,)
            ).fetchone()
            if not row:
                return False
            if row["default_visibility"] == "public":
                return True
            grant = con.execute(
                """SELECT * FROM data_grants
                   WHERE source_space_id = ? AND grantee_entity_id = ?
                   AND (valid_until = '' OR valid_until > ?)
                   AND (revoked_at = '' OR revoked_at > ?)""",
                (space_id, grantee_id, utc_now(), utc_now()),
            ).fetchone()
            return grant is not None


class PersonalReports:
    """Generate LifeGit/Wrapped/IdeaCemetery reports."""

    def __init__(self, db: Database):
        self.db = db

    def generate_wrapped(self, space_id: str, period_start: str, period_end: str) -> dict[str, Any]:
        from sandbox.semantic import SemanticObjectStore
        from sandbox.temporal import EventStore
        sem = SemanticObjectStore(self.db)
        events = EventStore(self.db).get_events_in_space(space_id)
        ideas = sem.list_objects(space_id=space_id, object_type="idea")
        questions = sem.list_objects(space_id=space_id, object_type="question")
        discoveries = sem.list_objects(space_id=space_id, object_type="discovery")
        return {
            "report_type": "life_wrapped",
            "space_id": space_id,
            "period": {"start": period_start, "end": period_end},
            "summary": {
                "total_events": len(events),
                "ideas_expressed": len(ideas),
                "questions_asked": len(questions),
                "discoveries": len(discoveries),
            },
            "events": events[:50],
            "ideas": ideas[:20],
        }

    def generate_idea_cemetery(self, space_id: str) -> dict[str, Any]:
        from sandbox.semantic import SemanticObjectStore
        sem = SemanticObjectStore(self.db)
        dormant = sem.find_dormant(space_id, days_threshold=30)
        return {
            "report_type": "idea_cemetery",
            "space_id": space_id,
            "dormant_ideas": dormant,
            "count": len(dormant),
        }
