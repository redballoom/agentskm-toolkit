#!/usr/bin/env python3
"""MCP stdio adapter for AgentsKM.

This server exposes KM CLI operations as MCP tools. It does not implement KM
rules directly; every tool call shells out to tools/km-cli/km.py --json.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
KM = ROOT / "tools" / "km-cli" / "km.py"
PROTOCOL_VERSION = "2025-06-18"
ROLE = "contributor"
ROLE_ORDER = {"contributor": 1, "reviewer": 2, "compiler": 3}


def main(argv: list[str] | None = None) -> int:
    global ROLE
    parser = argparse.ArgumentParser(prog="agentskm-mcp")
    parser.add_argument("--role", choices=sorted(ROLE_ORDER), default=os.environ.get("AGENTSKM_ROLE", "contributor"))
    args = parser.parse_args(argv)
    ROLE = args.role
    configure_utf8_stdio()
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            message = json.loads(raw)
            handle_message(message)
        except json.JSONDecodeError as exc:
            send_error(None, -32700, f"Parse error: {exc}")
        except Exception as exc:
            send_error(None, -32603, f"Internal error: {exc}")
    return 0


def handle_message(message: dict[str, Any]) -> None:
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}

    if request_id is None:
        return
    if method == "initialize":
        send_result(request_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {
                    "listChanged": False,
                },
            },
            "serverInfo": {
                "name": "agentskm",
                "version": "0.2.0",
            },
        })
        return
    if method == "ping":
        send_result(request_id, {})
        return
    if method == "tools/list":
        send_result(request_id, {"tools": tools()})
        return
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(tool_name, str):
            send_error(request_id, -32602, "tools/call requires params.name")
            return
        if not isinstance(arguments, dict):
            send_error(request_id, -32602, "tools/call params.arguments must be an object")
            return
        send_result(request_id, call_tool(tool_name, arguments))
        return
    send_error(request_id, -32601, f"Method not found: {method}")


def tools() -> list[dict[str, Any]]:
    available = [
        {
            "name": "km_configure_vault",
            "title": "Configure AgentsKM Vault",
            "description": "Persistently bind this toolkit installation to an existing local AgentsKM vault.",
            "inputSchema": object_schema({
                "vault": {"type": "string"},
                "dry_run": {"type": "boolean", "default": False},
            }, required=["vault"]),
        },
        {
            "name": "km_status",
            "title": "AgentsKM Status",
            "description": "Show repository counts by layer.",
            "inputSchema": object_schema({}),
        },
        {
            "name": "km_pending",
            "title": "List Pending Candidates",
            "description": "List active Inbox candidates that still need review.",
            "inputSchema": object_schema({}),
        },
        {
            "name": "km_reminders",
            "title": "Knowledge Reminders",
            "description": "List new candidates and snoozed candidates that are due again.",
            "inputSchema": object_schema({}),
        },
        {
            "name": "km_search",
            "title": "Search AgentsKM",
            "description": "Search Wiki, Inbox, Raw, docs, and tools. Wiki results are ranked first.",
            "inputSchema": object_schema({
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            }, required=["query"]),
        },
        {
            "name": "km_validate",
            "title": "Validate Frontmatter",
            "description": "Validate required frontmatter fields.",
            "inputSchema": object_schema({}),
        },
        {
            "name": "km_lint",
            "title": "Lint Links",
            "description": "Check internal wikilinks and misplaced formal pages.",
            "inputSchema": object_schema({}),
        },
        {
            "name": "km_propose_capture",
            "title": "Propose Knowledge Capture",
            "description": "Create an Inbox candidate. Use dry_run=true when only previewing.",
            "inputSchema": object_schema({
                "title": {"type": "string"},
                "value_reason": {"type": "string"},
                "type": {"type": "string", "default": "note"},
                "tags": {"type": "string", "description": "Comma-separated tags without implicit-capture."},
                "source_refs": {"type": "array", "items": {"type": "string"}},
                "suggested_target": {"type": "string"},
                "body": {"type": "string"},
                "agent_id": {"type": "string", "default": "mcp-agent"},
                "source_tool": {"type": "string", "default": "mcp"},
                "source_session": {"type": "string", "default": "mcp-session"},
                "confidence": {"type": "string", "enum": ["high", "medium", "low"], "default": "medium"},
                "sensitivity": {"type": "string", "enum": ["normal", "sensitive", "secret"], "default": "normal"},
                "dry_run": {"type": "boolean", "default": False},
            }, required=["title", "value_reason"]),
        },
    ]
    if ROLE_ORDER[ROLE] >= ROLE_ORDER["reviewer"]:
        available.extend([
            {
                "name": "km_review_candidate",
                "title": "Review Inbox Candidate",
                "description": "Record that a candidate was reminded, approved, snoozed, or rejected.",
                "inputSchema": object_schema({
                    "candidate": {"type": "string"},
                    "decision": {"type": "string", "enum": ["remind", "approve", "snooze", "reject"]},
                    "reviewed_by": {"type": "string"},
                    "reason": {"type": "string"},
                    "until": {"type": "string", "description": "YYYY-MM-DD; required for snooze."},
                    "dry_run": {"type": "boolean", "default": False},
                }, required=["candidate", "decision"]),
            },
            {
                "name": "km_dashboard",
                "title": "Refresh Review Dashboard",
                "description": "Generate the Obsidian review dashboard.",
                "inputSchema": object_schema({
                    "output": {"type": "string", "default": "docs/review-dashboard.md"},
                    "dry_run": {"type": "boolean", "default": False},
                }),
            },
        ])
    if ROLE_ORDER[ROLE] >= ROLE_ORDER["compiler"]:
        available.extend([
            {
                "name": "km_promote_candidate",
                "title": "Promote Inbox Candidate",
                "description": "Promote an approved Inbox candidate to a new Wiki page.",
                "inputSchema": approval_schema(require_target=False),
            },
            {
                "name": "km_merge_candidate",
                "title": "Merge Inbox Candidate",
                "description": "Merge an approved Inbox candidate into an existing Wiki page.",
                "inputSchema": approval_schema(require_target=True),
            },
        ])
    return available


def approval_schema(require_target: bool) -> dict[str, Any]:
    required = ["candidate", "approved_by", "scope"]
    if require_target:
        required.append("target")
    return object_schema({
        "candidate": {"type": "string"},
        "target": {"type": "string"},
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "approved_by": {"type": "string"},
        "scope": {"type": "string"},
        "dry_run": {"type": "boolean", "default": False},
    }, required=required)


def object_schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "km_status": ["status", "--json"],
        "km_pending": ["pending", "--json"],
        "km_reminders": ["reminders", "--json"],
        "km_validate": ["validate", "--json"],
        "km_lint": ["lint", "--json"],
    }
    if name in mapping:
        return cli_result(mapping[name])
    if name == "km_configure_vault":
        configure_args = ["configure", "--vault", require_string(args, "vault"), "--json"]
        if bool(args.get("dry_run", False)):
            configure_args.append("--dry-run")
        return cli_result(configure_args)
    if name == "km_search":
        return cli_result(["search", require_string(args, "query"), "--limit", str(args.get("limit", 10)), "--json"])
    if name == "km_propose_capture":
        return cli_result(build_propose_args(args))
    if name == "km_review_candidate" and ROLE_ORDER[ROLE] >= ROLE_ORDER["reviewer"]:
        return cli_result(build_review_args(args))
    if name == "km_promote_candidate":
        if ROLE_ORDER[ROLE] < ROLE_ORDER["compiler"]:
            raise ValueError("Compiler role is required")
        return cli_result(build_promote_args(args))
    if name == "km_merge_candidate":
        if ROLE_ORDER[ROLE] < ROLE_ORDER["compiler"]:
            raise ValueError("Compiler role is required")
        return cli_result(build_merge_args(args))
    if name == "km_dashboard":
        return cli_result(build_dashboard_args(args))
    raise ValueError(f"Unknown tool: {name}")


def cli_result(cli_args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [sys.executable, str(KM), *cli_args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        env=env,
        capture_output=True,
    )
    payload = parse_cli_json(proc.stdout, proc.stderr)
    is_error = proc.returncode != 0 or not bool(payload.get("ok", False))
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2),
            }
        ],
        "structuredContent": payload,
        "isError": is_error,
    }


def parse_cli_json(stdout: str, stderr: str) -> dict[str, Any]:
    text = stdout.strip()
    if text:
        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass
    return {
        "ok": False,
        "error": (stderr or stdout or "KM CLI returned no output").strip(),
    }


def build_propose_args(data: dict[str, Any]) -> list[str]:
    args = [
        "propose",
        "--title", require_string(data, "title"),
        "--value-reason", require_string(data, "value_reason"),
        "--actor-role", ROLE,
        "--json",
    ]
    append_option(args, data, "type", "--type")
    append_option(args, data, "tags", "--tags")
    append_option(args, data, "agent_id", "--agent-id")
    append_option(args, data, "source_tool", "--source-tool")
    append_option(args, data, "source_session", "--source-session")
    append_option(args, data, "suggested_target", "--suggested-target")
    append_option(args, data, "confidence", "--confidence")
    append_option(args, data, "sensitivity", "--sensitivity")
    append_option(args, data, "body", "--body")
    for source_ref in string_list(data.get("source_refs")):
        args.extend(["--source-ref", source_ref])
    if bool(data.get("dry_run", False)):
        args.append("--dry-run")
    return args


def build_promote_args(data: dict[str, Any]) -> list[str]:
    args = ["promote", require_string(data, "candidate"), "--actor-role", ROLE, "--json"]
    append_option(args, data, "target", "--target")
    append_option(args, data, "title", "--title")
    append_option(args, data, "summary", "--summary")
    args.extend(["--approved-by", require_string(data, "approved_by")])
    args.extend(["--scope", require_string(data, "scope")])
    if bool(data.get("dry_run", False)):
        args.append("--dry-run")
    return args


def build_review_args(data: dict[str, Any]) -> list[str]:
    args = [
        "review",
        require_string(data, "candidate"),
        "--decision", require_string(data, "decision"),
        "--actor-role", ROLE,
        "--json",
    ]
    append_option(args, data, "reviewed_by", "--reviewed-by")
    append_option(args, data, "reason", "--reason")
    append_option(args, data, "until", "--until")
    if bool(data.get("dry_run", False)):
        args.append("--dry-run")
    return args


def build_merge_args(data: dict[str, Any]) -> list[str]:
    args = [
        "merge",
        require_string(data, "candidate"),
        "--target", require_string(data, "target"),
        "--approved-by", require_string(data, "approved_by"),
        "--scope", require_string(data, "scope"),
        "--actor-role", ROLE,
        "--json",
    ]
    if bool(data.get("dry_run", False)):
        args.append("--dry-run")
    return args


def build_dashboard_args(data: dict[str, Any]) -> list[str]:
    args = ["dashboard", "--actor-role", ROLE, "--json"]
    append_option(args, data, "output", "--output")
    if bool(data.get("dry_run", False)):
        args.append("--dry-run")
    return args


def require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing required string field: {key}")
    return value


def append_option(args: list[str], data: dict[str, Any], key: str, flag: str) -> None:
    value = data.get(key)
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError(f"Field must be a string: {key}")
    if value:
        args.extend([flag, value])


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("source_refs must be a list of strings")
    return [item for item in value if item]


def send_result(request_id: Any, result: dict[str, Any]) -> None:
    send({"jsonrpc": "2.0", "id": request_id, "result": result})


def send_error(request_id: Any, code: int, message: str) -> None:
    send({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})


def send(message: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def configure_utf8_stdio() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
