"""LifeGit V0 suite tests — adapted from lifegit_bundle."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sandbox.lifegit.db import LifeDB
from sandbox.lifegit.extract import run_extraction
from sandbox.lifegit.providers.chatgpt import ChatGPTProvider
from sandbox.lifegit.providers.claude import ClaudeProvider
from sandbox.lifegit.qdw_export import export_qdw_jsonl
from sandbox.lifegit.enrichment import export_batches, apply_results
from sandbox.lifegit.pastme import snapshot
from sandbox.lifegit.api import query
from sandbox.lifegit.reports import generate_all

FIX = Path(__file__).parent / "fixtures"


class TestLifeGit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = LifeDB(self.root / "life.db")

    def tearDown(self):
        self.tmp.cleanup()

    def _import_both(self):
        for provider, path in [
            (ChatGPTProvider(), FIX / "chatgpt_conversations.json"),
            (ClaudeProvider(), FIX / "claude_conversations.json"),
        ]:
            convs, sha, member = provider.parse(path)
            self.db.import_conversations(
                convs, artifact_sha=sha, provider=provider.name,
                source_path=str(path), member_name=member,
            )

    def test_chatgpt_mapping_parser(self):
        convs, _, _ = ChatGPTProvider().parse(FIX / "chatgpt_conversations.json")
        self.assertEqual(len(convs), 2)
        self.assertEqual(convs[0].messages[0].role, "user")
        self.assertTrue(any(m.model == "gpt-test" for m in convs[0].messages))
        self.assertTrue(all(m.is_current_path for m in convs[0].messages))

    def test_claude_parser(self):
        convs, _, _ = ClaudeProvider().parse(FIX / "claude_conversations.json")
        self.assertEqual(len(convs), 1)
        self.assertEqual([m.role for m in convs[0].messages], ["user", "assistant", "user"])
        self.assertIn("work-safe", convs[0].messages[-1].text)

    def test_import_extract_reports(self):
        self._import_both()
        result = run_extraction(self.db)
        self.assertGreater(result["semantic_objects"], 5)
        stats = self.db.stats()
        self.assertEqual(stats["conversations"], 3)
        self.assertGreater(stats["messages"], 5)
        self.assertGreater(stats["tensions"], 0)
        out = self.root / "reports"
        manifest = generate_all(self.db, out)
        self.assertTrue((out / "index.html").exists())
        self.assertTrue((out / "ideas.html").exists())
        self.assertTrue((out / "career.html").exists())
        self.assertIn("reports", manifest)
        career = (out / "career.html").read_text()
        self.assertIn("evidence", career.lower())

    def test_provenance_and_private_default(self):
        self._import_both()
        run_extraction(self.db)
        with self.db.connect() as con:
            rows = con.execute("SELECT * FROM semantic_objects").fetchall()
        self.assertTrue(rows)
        self.assertTrue(all(r["evidence_message_id"] for r in rows))
        self.assertTrue(all(r["privacy_class"] in {"PRIVATE", "WORK_CANDIDATE"} for r in rows))

    def test_qdw_export_retains_private_space(self):
        self._import_both()
        run_extraction(self.db)
        out = self.root / "qdw.jsonl"
        result = export_qdw_jsonl(self.db, out, space_id="life:test-user")
        self.assertGreater(result["records"], 0)
        records = [json.loads(x) for x in out.read_text().splitlines()]
        self.assertTrue(all(r["space_id"] == "life:test-user" for r in records))
        semantic = [r for r in records if r["record_type"] == "semantic_object"]
        self.assertTrue(all("evidence" in r for r in semantic))

    def test_enrichment_contract(self):
        self._import_both()
        batch = self.root / "batch.jsonl"
        result = export_batches(self.db, batch)
        self.assertEqual(result["messages"], 6)
        first = json.loads(batch.read_text().splitlines()[0])
        enriched = self.root / "enriched.jsonl"
        enriched.write_text(json.dumps({
            "message_id": first["message_id"],
            "objects": [{
                "object_type": "IDEA",
                "canonical_text": "Build a provenance-backed personal timeline",
                "confidence": 0.91,
                "work_relevance": 0.5,
                "attributes": {"source": "mock"},
            }],
        }) + "\n")
        applied = apply_results(self.db, enriched, extractor_version="mock-v1")
        self.assertEqual(applied["objects_applied"], 1)
        with self.db.connect() as con:
            row = con.execute("SELECT * FROM semantic_objects WHERE extractor_version='mock-v1'").fetchone()
        self.assertEqual(row["evidence_message_id"], first["message_id"])

    def test_past_me_is_time_bounded(self):
        self._import_both()
        run_extraction(self.db)
        early = snapshot(self.db, "2025-02-01")
        late = snapshot(self.db, "2025-06-01")
        self.assertLess(len(early["semantic_objects"]), len(late["semantic_objects"]))

    def test_read_only_api_query(self):
        self._import_both()
        run_extraction(self.db)
        status, body = query(self.db, "/stats", {})
        self.assertEqual(status, 200)
        self.assertEqual(body["conversations"], 3)
        status, ideas = query(self.db, "/objects", {"type": ["IDEA"]})
        self.assertEqual(status, 200)
        self.assertTrue(all(x["object_type"] == "IDEA" for x in ideas))


if __name__ == "__main__":
    unittest.main()
