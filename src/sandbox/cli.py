"""QDW Sandbox CLI — verification and management commands."""

from __future__ import annotations

import json
import sys


def cmd_doctor(args: list[str]) -> int:
    from sandbox.system import SandboxSystem
    sys_db = args[0] if args else "data/sandbox.db"
    system = SandboxSystem(sys_db)
    result = system.doctor()
    print(json.dumps(result, indent=2))
    return 0


def cmd_bounty(args: list[str]) -> int:
    from sandbox.system import SandboxSystem
    from sandbox.types import BountySpec, BountyType, SubmissionFormat, new_id

    if not args or args[0] not in ("create", "list", "open", "evaluate"):
        print("Usage: sandbox bounty <create|list|open|evaluate> [args...]")
        return 1

    system = SandboxSystem("data/sandbox.db")
    action = args[0]

    if action == "create":
        if len(args) < 6:
            print("Usage: sandbox bounty create <type> <title> <description> <requirement> <budget_usd> <deadline_seconds>")
            return 1
        spec = BountySpec(
            bounty_id=new_id("bounty"),
            bounty_type=BountyType(args[1]),
            title=args[2],
            description=args[3],
            requirement=args[4],
            budget_usd=float(args[5]),
            deadline_seconds=int(args[6]) if len(args) > 6 else 3600,
            submission_format=SubmissionFormat(),
        )
        system.bounties.create_bounty(spec)
        print(f"Created: {spec.bounty_id}")
        return 0

    if action == "list":
        bounties = system.bounties.list_bounties(args[1] if len(args) > 1 else None)
        for b in bounties:
            print(f"  {b['bounty_id']} [{b['status']}] {b['title']} (${b['budget_usd']})")
        return 0

    if action == "open":
        if len(args) < 2:
            print("Usage: sandbox bounty open <bounty_id>")
            return 1
        system.bounties.open_bounty(args[1])
        print("Opened")
        return 0

    if action == "evaluate":
        if len(args) < 2:
            print("Usage: sandbox bounty evaluate <bounty_id>")
            return 1
        evals = system.bounty_resolver.evaluate_options(args[1])
        for e in evals:
            print(f"  {e.resource_type.value}: ${e.expected_cost_usd:.2f} conf={e.confidence:.2f}")
        return 0

    return 1


def cmd_worker(args: list[str]) -> int:
    from sandbox.system import SandboxSystem

    if not args:
        print("Usage: sandbox worker <list|register> [args...]")
        return 1

    system = SandboxSystem("data/sandbox.db")

    if args[0] == "list":
        workers = system.human_oracle.workers.list_workers()
        for w in workers:
            print(f"  {w['worker_id']} rep={w['reputation']:.2f} tasks={w['total_tasks']}")
        return 0

    if args[0] == "register":
        if len(args) < 3:
            print("Usage: sandbox worker register <worker_id> <cap1,cap2,...>")
            return 1
        from sandbox.types import WorkerCapability
        caps = [WorkerCapability(c) for c in args[2].split(",")]
        system.human_oracle.workers.register_worker(args[1], caps)
        print(f"Registered: {args[1]}")
        return 0

    return 1


def cmd_rights(args: list[str]) -> int:
    from sandbox.system import SandboxSystem

    if not args:
        print("Usage: sandbox rights <list|check> [args...]")
        return 1

    system = SandboxSystem("data/sandbox.db")
    backend = system.get_rights_backend()

    if args[0] == "list":
        licences = backend.list_licences(args[1] if len(args) > 1 else None)
        for l in licences:
            print(f"  {l['licence_id']} asset={l['asset_id']} purpose={l['purpose']} ${l['price_usd']}")
        return 0

    if args[0] == "check":
        if len(args) < 4:
            print("Usage: sandbox rights check <asset_id> <purpose> <op1,op2,...>")
            return 1
        from sandbox.types import LicenseOperation
        ops = [LicenseOperation(o) for o in args[3].split(",")]
        cr = backend.check_clearance(args[1], args[2], ops)
        print(f"  granted={cr.granted} reason={cr.reason}")
        return 0

    return 1


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: sandbox <command> [args...]")
        print("Commands: doctor, bounty, worker, rights")
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "doctor":
        return cmd_doctor(args)
    elif command == "bounty":
        return cmd_bounty(args)
    elif command == "worker":
        return cmd_worker(args)
    elif command == "rights":
        return cmd_rights(args)
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
