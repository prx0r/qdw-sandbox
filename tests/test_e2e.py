"""E2E tests: market→product, lifegit→wrapped, lifegit→market, human→world, cemetery revival."""

import tempfile
import os
import pytest

from sandbox.system import SandboxSystem
from sandbox.types import (
    SemanticObjectType, ThreadStatus, new_id, utc_now,
)


def make_system(tmp_path):
    return SandboxSystem(os.path.join(tmp_path, "test.db"))


# ── 1. Market reality → Product ───────────────────────────────────────────


def test_market_reality_to_product(tmp_path):
    sys = make_system(tmp_path)

    sys.spaces.create_space("world:public", "world")

    tension = sys.tensions.create_tension(
        space_id="world:public",
        subject_segment="heavy_ai_users",
        dimension="information_retrieval",
        observed_state_concept="valuable_ideas_fragmented_across_chats",
        desired_state_concept="valuable_ideas_recoverable",
        prevalence=0.31, recurrence=0.74, severity=0.56,
        persistence=0.81, confidence=0.87,
    )

    sys.edges.add_edge("tension", tension.tension_id, "addresses",
                       "dimension", "information_retrieval")
    score = sys.tensions.score_opportunity(tension.tension_id)
    assert score is not None
    assert score["opportunity_score"] > 0

    idea = sys.semantic.create_object(
        space_id="world:public",
        object_type=SemanticObjectType.IDEA,
        canonical_key="resurface_history",
        content={"mechanism": "temporal_clustering", "addresses": tension.tension_id},
    )
    assert idea.object_id.startswith("semobj_")

    sys.edges.add_edge("idea", idea.object_id, "addresses",
                       "tension", tension.tension_id)

    edges = sys.edges.get_edges_from("idea", idea.object_id)
    assert len(edges) == 1
    assert edges[0]["object_id"] == tension.tension_id


# ── 2. LifeGit → Wrapped ─────────────────────────────────────────────────


def test_lifegit_to_wrapped(tmp_path):
    sys = make_system(tmp_path)

    # Create private space
    sys.spaces.create_space("life:tom", "life", owner_entity_id="tom")

    # Ingest ChatGPT messages
    messages = [
        {"role": "user", "content": "I have a brilliant idea for a product that uses temporal clustering to resurface valuable AI conversations from months ago so developers never lose good ideas"},
        {"role": "assistant", "content": "That's an interesting idea..."},
        {"role": "user", "content": "How do I recover old ChatGPT conversations that had valuable ideas I can no longer find in my history?"},
    ]
    result = sys.personal_ingest.ingest_chatgpt_export("life:tom", messages)
    assert result["ingested"] == 3

    ideas = sys.personal_extract.extract_ideas("life:tom")
    discoveries = sys.semantic.list_objects(space_id="life:tom", object_type="discovery")
    assert len(ideas) >= 1
    assert len(discoveries) >= 1

    # Generate Wrapped report
    report = sys.personal_reports.generate_wrapped("life:tom", "2026-01-01", "2026-12-31")
    assert report["report_type"] == "life_wrapped"
    assert report["summary"]["ideas_expressed"] >= 1
    assert report["summary"]["total_events"] + report["summary"]["ideas_expressed"] + report["summary"]["discoveries"] >= 3


# ── 3. LifeGit → Market with consent ─────────────────────────────────────


def test_lifegit_to_market_with_consent(tmp_path):
    sys = make_system(tmp_path)

    # Private space
    sys.spaces.create_space("life:tom", "life", owner_entity_id="tom")

    # Public space
    sys.spaces.create_space("world:public", "world")

    # Private tension
    tension = sys.tensions.create_tension(
        space_id="life:tom",
        subject_segment="personal",
        dimension="information_retrieval",
        observed_state_concept="lost_chatgpt_ideas",
        desired_state_concept="recovered_ideas",
        prevalence=0.9, severity=0.8, confidence=0.95,
    )

    # Grant access for market aggregation
    grant = sys.grants.create_grant(
        owner_entity_id="tom",
        source_space_id="life:tom",
        grantee_entity_id="market_aggregator",
        purpose_term_id="aggregate_research",
        scope={"tension_id": tension.tension_id},
        allowed_operations=("aggregate", "classify"),
    )
    assert grant.grant_id.startswith("grant_")

    # Check access
    check = sys.grants.check_grant("life:tom", "market_aggregator", "aggregate_research")
    assert check is not None
    assert check["grant_id"] == grant.grant_id

    # Verify raw private data is not directly queryable from public
    public_tensions = sys.tensions.list_tensions(space_id="world:public")
    assert len(public_tensions) == 0


# ── 4. Human sensor → World ──────────────────────────────────────────────


def test_human_sensor_to_world(tmp_path):
    sys = make_system(tmp_path)

    # Register worker
    from sandbox.types import WorkerCapability
    sys.human_oracle.workers.register_worker(
        "researcher_1",
        [WorkerCapability.RESEARCH, WorkerCapability.COMPREHENSION_TEST],
    )

    # Log human task
    sys.human_oracle.router.log_task(
        "bounty_1", "researcher_1", "completed",
        {"result": "found_20_examples", "quality": 0.92},
    )

    # Verify task was logged
    from sandbox.core import Database
    with sys.db.connect() as con:
        rows = con.execute("SELECT * FROM human_task_log").fetchall()
        assert len(rows) == 1
        assert rows[0]["action"] == "completed"


# ── 5. Cemetery capability revival ────────────────────────────────────────


def test_cemetery_capability_revival(tmp_path):
    sys = make_system(tmp_path)

    sys.spaces.create_space("world:public", "world")

    # Create a dormant idea
    idea = sys.semantic.create_object(
        space_id="world:public",
        object_type=SemanticObjectType.IDEA,
        canonical_key="old_idea_dormant",
        content={"status": "dormant"},
    )

    # Manually age it by updating last_observed_at
    with sys.db.tx() as con:
        con.execute(
            "UPDATE semantic_objects SET last_observed_at = ? WHERE object_id = ?",
            ("2025-01-01T00:00:00+00:00", idea.object_id),
        )

    # Find dormant ideas
    dormant = sys.semantic.find_dormant("world:public", days_threshold=30)
    assert len(dormant) >= 1
    assert dormant[0]["object_id"] == idea.object_id

    # Promote it (simulates revival)
    promoted = sys.semantic.promote_to_hypothesis(idea.object_id)
    assert promoted is not None
    assert promoted["object_type_term_id"] == "hypothesis"
    assert promoted["status"] == "promoted"


# ── 6. Spaces and privacy ────────────────────────────────────────────────


def test_spaces_and_privacy(tmp_path):
    sys = make_system(tmp_path)

    sys.spaces.create_space("life:tom", "life", owner_entity_id="tom", default_visibility="private")
    sys.spaces.create_space("world:public", "world", default_visibility="public")

    # Public is accessible to all
    assert sys.personal_privacy.check_access("world:public", "anyone")

    # Private requires grant
    assert not sys.personal_privacy.check_access("life:tom", "stranger")

    sys.grants.create_grant(
        owner_entity_id="tom", source_space_id="life:tom",
        grantee_entity_id="friend_1", purpose_term_id="view_profile",
    )
    assert sys.personal_privacy.check_access("life:tom", "friend_1")


# ── 7. Ontology and edges ────────────────────────────────────────────────


def test_ontology_and_edges(tmp_path):
    sys = make_system(tmp_path)

    # Default ontology seeded
    terms = sys.ontology.list_terms(kind="predicate")
    assert len(terms) >= 10

    # Create tension and idea, link with edges
    sys.spaces.create_space("world:public", "world")
    tension = sys.tensions.create_tension(
        space_id="world:public", subject_segment="devs",
        dimension="developer_productivity",
        observed_state_concept="manual_config",
        desired_state_concept="auto_config",
    )
    idea = sys.semantic.create_object(
        space_id="world:public", object_type=SemanticObjectType.IDEA,
        canonical_key="auto_config_tool",
    )
    sys.edges.add_edge("idea", idea.object_id, "addresses", "tension", tension.tension_id)

    # Query edges
    out = sys.edges.get_edges_from("idea", idea.object_id)
    assert len(out) == 1
    into = sys.edges.get_edges_to("tension", tension.tension_id)
    assert len(into) == 1


# ── 8. Threads ───────────────────────────────────────────────────────────


def test_threads(tmp_path):
    sys = make_system(tmp_path)

    sys.spaces.create_space("life:tom", "life")
    thread = sys.threads.create_thread("life:tom", "problem_thread", "problem_1")
    sys.threads.add_member(thread.thread_id, "event", "evt_1", ordinal=1)
    sys.threads.add_member(thread.thread_id, "event", "evt_2", ordinal=2)

    members = sys.threads.get_members(thread.thread_id)
    assert len(members) == 2
    assert members[0]["ordinal"] < members[1]["ordinal"]
