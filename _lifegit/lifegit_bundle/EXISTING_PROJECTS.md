# Existing exported-LLM-data projects: what to use

## 1. `owrew/ConvoVault` — use as provider-architecture reference

**Why:** MIT licensed; provider-independent core; separate ChatGPT/Claude/Gemini/etc adapters; clean plugin boundary; chronological/indexing ideas.

**Use:** port/adapt parsing tests or provider-interface patterns when a new export format appears. Keep LifeGit's canonical model separate so a provider can be replaced without changing reports.

**Do not:** make Obsidian/Markdown its permanent data model. LifeGit needs temporal objects, evidence edges, privacy spaces and report projections.

## 2. `otonashi-labs/chatgpt-wrapped` — use as analytics/enrichment reference

**Why:** strong concept: deterministic unroll first, then LLM metadata; handles large histories and multi-year timelines; rich per-conversation fields.

**Use:** inspiration for batch enrichment taxonomy, cost-conscious processing and dashboard metrics.

**Caution:** the README describes MIT, but the inspected repository root did not contain a LICENSE file. Treat code reuse as unresolved until the repository has an explicit license file; architectural ideas are fine to reimplement.

## 3. `1ch1n/mychatarchive` — run standalone or study, do not embed into a permissive commercial core

**Why:** excellent local-first SQLite/FTS/vector archive; multi-provider import; MCP; sensitivity levels; semantic search.

**License:** AGPL-3.0.

**Use:** optional separate service/process if you deliberately accept its licensing obligations, or as inspiration for local search/MCP UX.

**Do not:** copy its code into a proprietary/permissively-licensed LifeGit server unless you intentionally adopt/comply with AGPL obligations.

## 4. `Robbings/chatgpt-graph-navigator` — UI inspiration only

**Why:** conversation-tree and Git-style timeline visualization is relevant to LifeGit.

**Use:** study interaction patterns for navigating branches/history.

**Do not:** confuse conversation branching with the LifeGit semantic graph; our graph links questions, ideas, projects, problems and evidence across conversations.

## 5. Claude conversation analyzers / simple ChatGPT Wrapped clones

Useful mainly as regression fixtures and UX comparison: client-side parsing, date filters, activity heatmaps, share cards. They are not the semantic-life layer.

# Recommended stack

Start with this bundle's own canonical parser + DB. Use ConvoVault as the first reference when we need additional providers. Keep MyChatArchive external. Add an LLM enrichment runner only after your real export has established parser fixtures and deterministic counts.
