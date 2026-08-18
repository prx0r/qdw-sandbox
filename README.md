# QDW Sandbox

Development playground for bounty engine, human oracle, and data rights primitives that will graduate into the QDW core stack.

## Quick Start

```bash
pip install -e ".[dev]"
sandbox doctor
```

## Modules

- **Bounty Engine** — 4 bounty types: TASK, DATA, EVIDENCE, ASSET
- **HumanOracle** — route tasks to humans as capability providers
- **DataRightsBackend** — abstract data licensing (NativeLocal, Vana, EnterpriseVault)
- **StackOracle** — allocate resources across LLM/tool/human/data providers

## CLI

```bash
sandbox doctor                                    # system health
sandbox bounty create evidence "Find X" ...       # create bounty
sandbox bounty list                                # list bounties
sandbox worker list                                # list workers
sandbox rights check <asset_id> <purpose> <ops>   # check data clearance
```

## API

```bash
uvicorn sandbox.interfaces.api:app --port 8000
```

## Architecture

```
                    STACK ORACLE
                         │
     ┌───────────────────┼───────────────────┐
     │                   │                   │
     ▼                   ▼                   ▼
HumanOracle        DataRights          BountyEngine
     │               Backend                │
     │                   │                   │
 humans             licences            verify/issue
 sensors            datasets            certificates
 observations       repositories        ──────────→ QDW
```
