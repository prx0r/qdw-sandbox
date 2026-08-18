# LifeGit Wrapped Suite — V0

A local-first, provenance-backed foundation for turning exported LLM history into structured personal history.

This bundle intentionally separates **raw evidence** from **derived semantic objects**. It does not treat an LLM-written biography as truth. Every extracted question, idea, problem, project or work claim points back to source conversation/message IDs.

## Included products

All products are thin report/projection layers over the same SQLite graph:

- **LifeGit** — canonical personal conversation/event store and timeline.
- **Life Wrapped** — year/period review: activity, recurring themes, questions, ideas, projects and evidence-linked highlights.
- **Idea Cemetery** — ideas detected in your conversations, including repeat/rediscovery signals.
- **My Questions** — questions you asked, clustered approximately and placed on a timeline.
- **Problem Ledger** — recurring explicit problems/frictions and their last-seen dates.
- **CareerGit** — work-safe projection of projects, research, skills and achievements; raw chat is not exposed.
- **Past Me** — date-bounded search/export so later agents can reason only from what existed by a historical date.
- **Memory Diff** — semantic-object additions/disappearances between two periods.

## Why this implementation

Existing projects are useful but fragmented. `otonashi-labs/chatgpt-wrapped` demonstrates deterministic unrolling + semantic metadata and multi-year visual analysis. `owrew/ConvoVault` demonstrates a strong provider plugin boundary and unified conversation model. `1ch1n/mychatarchive` demonstrates excellent local archive/search/MCP ideas, but its AGPL-3.0 license makes direct reuse undesirable for a potentially commercial hosted LifeGit product. This bundle is therefore a clean-room implementation using only the architectural lessons.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
# offline environments with setuptools already installed: pip install -e . --no-build-isolation

# ChatGPT export ZIP or conversations.json
lifegit build-all ~/Downloads/chatgpt-export.zip --provider chatgpt --db life.db --out reports

# Claude export
lifegit build-all ~/Downloads/claude-export.zip --provider claude --db life.db --out reports
```

Then open `reports/index.html`.

You can import multiple providers into the same DB:

```bash
lifegit import chatgpt.zip --provider chatgpt --db life.db
lifegit import claude.zip --provider claude --db life.db
lifegit extract --db life.db
lifegit reports --db life.db --out reports
```

## Data model

The permanent raw layer is:

`source_artifact -> conversation -> message`

Derived layers are rebuildable:

`message -> semantic_object -> object_link / event / tension -> report`

Semantic object types in V0:

`QUESTION, IDEA, PROBLEM, PROJECT, DISCOVERY, DECISION, GOAL, ACHIEVEMENT, WORK_CLAIM`

Each derived row has `evidence_message_id`, `extractor_version`, and `confidence`.

## Privacy model

- Raw source data stays in your local SQLite database.
- Reports use snippets, not entire conversations.
- CareerGit only includes objects classified as work-related by deterministic rules in V0.
- No diagnosis/personality inference is performed.
- Nothing is uploaded by this package.

## QDW integration

`qdw_patch/` contains a proposed semantic-core migration and integration notes. `lifegit qdw-export` emits JSONL records designed to map onto QDW observations/events/semantic objects while preserving a private `space_id`.

## Limitations of V0

- Semantic extraction is deliberately conservative and deterministic. It is good enough to validate schemas and your own export before adding an LLM enrichment pass.
- Similarity/rediscovery uses normalized-token Jaccard matching rather than embeddings.
- ChatGPT exports evolve. The parser supports the common `mapping/current_node` graph form and flat message fallbacks, but real exports should be retained as regression fixtures when new variants appear.
- Work/private classification is conservative and should always be reviewed before sharing.

## Test

```bash
python -m unittest discover -s tests -v
```

## Local API / agent access

```bash
lifegit serve --db life.db --port 8787
```

Read-only endpoints: `/health`, `/stats`, `/objects?type=IDEA`, `/tensions`, `/career`, `/past?at=2025-01-01`.

V0 binds to `127.0.0.1` by default. Do not expose a personal database to the public internet without an authentication/grant layer.
