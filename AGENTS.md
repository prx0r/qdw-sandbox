# AGENTS.md — QDW Sandbox

*Development playground for bounty engine, human oracle, and data rights primitives.*

---

## THE ONE RULE

> **Nothing is DONE because code exists or because you say a test passed.**
> It is PROVEN only when a recorded verification run shows every required gate passed.

---

## WHAT THIS REPO IS

QDW Sandbox is where we develop and test modules before they graduate into the QDW core stack. It contains:

| Module | Purpose |
|---|---|
| `sandbox/bounty/` | Bounty Engine — 4 bounty types (TASK, DATA, EVIDENCE, ASSET) |
| `sandbox/human/` | HumanOracle — route tasks to humans as capability providers |
| `sandbox/data_rights/` | DataRightsBackend — abstract data licensing (NativeLocal, Vana, EnterpriseVault) |
| `sandbox/oracle/` | StackOracle — allocate resources across LLM/tool/human/data providers |
| `sandbox/system.py` | Single composition root — all DI happens here |
| `sandbox/interfaces/` | Thin API + MCP — zero business logic |

---

## INTEGRATION WITH QDW

When a module is stable and verified, it graduates to QDW core:

```
sandbox/bounty/    →    qdw/src/qdw/bounty/
sandbox/human/     →    qdw/src/qdw/human/
sandbox/data_rights/ →  qdw/src/qdw/data_rights/
sandbox/oracle/    →    qdw/src/qdw/oracle/
```

QDW integration points:
- `BountySpec` extends `TaskSpec` with `bounty_usd`, `deadline`, `submission_format`
- HumanOracle routes are `Route` with `provider_id="human"`
- DataRightsBackend plugs into `Gate` verification system
- StackOracle extends `HotSwapRouter` with resource allocation

---

## ANTI-CHEAT RULES

Same as QDW core. See `qdw/AGENTS.md` for full list.

Key invariants:
- No synthetic data
- No mock certificates
- Content hashes required for all artifacts
- PASS is calculated, never asserted by the agent
- Every bounty result must pass verification gates

---

## VERIFICATION LADDER

Same V0–V12 as QDW. Bounty results must pass at minimum V0–V5.

---

## FILE CONVENTIONS

| Thing | Location |
|---|---|
| Source | `src/sandbox/` |
| Tests | `tests/` |
| Migrations | `migrations/NNNN_name.sql` |
| API | `src/sandbox/interfaces/api.py` |
| MCP | `src/sandbox/interfaces/mcp_server.py` |
| CLI | `src/sandbox/cli.py` |
