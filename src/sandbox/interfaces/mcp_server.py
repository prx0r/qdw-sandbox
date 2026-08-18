"""QDW Sandbox MCP server — thin interface over SandboxSystem."""

from __future__ import annotations

import json
from typing import Any

MCP_TOOLS = [
    {
        "name": "sandbox_get_status",
        "description": "Get sandbox system status and health",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "sandbox_list_bounties",
        "description": "List bounties optionally filtered by status",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by status (draft, open, submitted, etc.)"},
            },
        },
    },
    {
        "name": "sandbox_create_bounty",
        "description": "Create a new bounty",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bounty_type": {"type": "string", "enum": ["task", "data", "evidence", "asset"]},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "requirement": {"type": "string"},
                "budget_usd": {"type": "number"},
                "deadline_seconds": {"type": "integer"},
            },
            "required": ["bounty_type", "title", "description", "requirement", "budget_usd", "deadline_seconds"],
        },
    },
    {
        "name": "sandbox_resolve_human",
        "description": "Find human workers for a capability",
        "inputSchema": {
            "type": "object",
            "properties": {
                "capability": {"type": "string"},
                "budget_usd": {"type": "number"},
                "deadline_seconds": {"type": "integer"},
            },
            "required": ["capability"],
        },
    },
    {
        "name": "sandbox_check_rights",
        "description": "Check data rights clearance for an asset",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string"},
                "purpose": {"type": "string"},
                "operations": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["asset_id", "purpose", "operations"],
        },
    },
]


_system: Any = None


def _get_system():
    global _system
    if _system is None:
        from sandbox.system import SandboxSystem
        _system = SandboxSystem("data/sandbox.db")
    return _system


def handle_mcp_request(method: str, params: dict[str, Any]) -> dict[str, Any]:
    if method == "tools/list":
        return {"tools": MCP_TOOLS}

    if method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})
        return _call_tool(tool_name, args)

    return {"error": f"unknown method: {method}"}


def _call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    sys = _get_system()

    if name == "sandbox_get_status":
        return {"content": [{"type": "text", "text": json.dumps(sys.doctor(), indent=2)}]}

    if name == "sandbox_list_bounties":
        bounties = sys.bounties.list_bounties(args.get("status"))
        return {"content": [{"type": "text", "text": json.dumps(bounties, indent=2)}]}

    if name == "sandbox_create_bounty":
        from sandbox.types import BountySpec, BountyType, SubmissionFormat, new_id
        spec = BountySpec(
            bounty_id=new_id("bounty"),
            bounty_type=BountyType(args["bounty_type"]),
            title=args["title"],
            description=args["description"],
            requirement=args["requirement"],
            budget_usd=args["budget_usd"],
            deadline_seconds=args["deadline_seconds"],
            submission_format=SubmissionFormat(),
        )
        sys.bounties.create_bounty(spec)
        return {"content": [{"type": "text", "text": json.dumps({"bounty_id": spec.bounty_id})}]}

    if name == "sandbox_resolve_human":
        from sandbox.types import WorkerCapability
        cap = WorkerCapability(args["capability"])
        results = sys.human_oracle.resolve(
            args.get("description", ""),
            cap,
            args.get("budget_usd", 100.0),
            args.get("deadline_seconds", 3600),
        )
        return {"content": [{"type": "text", "text": json.dumps(results, indent=2)}]}

    if name == "sandbox_check_rights":
        from sandbox.types import LicenseOperation
        ops = [LicenseOperation(o) for o in args["operations"]]
        cr = sys.get_rights_backend().check_clearance(args["asset_id"], args["purpose"], ops)
        return {"content": [{"type": "text", "text": json.dumps({"granted": cr.granted, "reason": cr.reason})}]}

    return {"error": f"unknown tool: {name}"}
