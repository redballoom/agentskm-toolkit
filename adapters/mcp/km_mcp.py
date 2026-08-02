#!/usr/bin/env python3
"""MCP stdio adapter for AgentsKM.

This server exposes KM CLI operations as MCP tools. It does not implement KM
rules directly; every tool call shells out to tools/km-cli/km.py --json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
KM = ROOT / "tools" / "km-cli" / "km.py"
PROTOCOL_VERSION = "2025-06-18"
ROLE = "contributor"
PROFILE = "default"
HOST = "generic"
CONFIG_PATH = ""
SETUP_STATUS: dict[str, Any] = {}
ROLE_ORDER = {"contributor": 1, "reviewer": 2, "compiler": 3}


def main(argv: list[str] | None = None) -> int:
    global PROFILE, ROLE, HOST, CONFIG_PATH, SETUP_STATUS
    parser = argparse.ArgumentParser(prog="agentskm-mcp")
    parser.add_argument("--profile", default="default")
    parser.add_argument("--host", default="generic")
    parser.add_argument("--bootstrap-role", choices=sorted(ROLE_ORDER), default="contributor")
    parser.add_argument("--config")
    args = parser.parse_args(argv)
    PROFILE = args.profile
    HOST = args.host
    CONFIG_PATH = str(Path(args.config).expanduser().resolve()) if args.config else ""
    SETUP_STATUS = load_setup_status(PROFILE)
    if SETUP_STATUS.get("state") in {"config_missing", "profile_missing"}:
        bootstrap_profile(PROFILE, HOST, args.bootstrap_role)
        SETUP_STATUS = load_setup_status(PROFILE)
    if SETUP_STATUS.get("configured"):
        ROLE = str(SETUP_STATUS["role"])
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
                "version": "0.4.4",
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
        try:
            send_result(request_id, call_tool(tool_name, arguments))
        except (FileExistsError, FileNotFoundError, PermissionError, RuntimeError, ValueError) as exc:
            send_result(request_id, tool_payload({
                "ok": False,
                "error": str(exc),
                "error_type": exc.__class__.__name__,
            }, is_error=True))
        return
    send_error(request_id, -32601, f"Method not found: {method}")


def tools() -> list[dict[str, Any]]:
    refresh_setup_status()
    setup_tool = {
        "name": "km_setup_status",
        "title": "Check AgentsKM Setup",
        "description": "Check the selected Agent Profile and Vault without modifying user configuration.",
        "inputSchema": object_schema({}),
    }
    if not SETUP_STATUS.get("configured"):
        return [
            setup_tool,
            doctor_tool(),
            update_tool(),
            {
                "name": "km_setup_instructions",
                "title": "Show AgentsKM Setup Instructions",
                "description": "Show the exact local CLI entry point and the missing setup information. This tool never writes configuration.",
                "inputSchema": object_schema({}),
            },
        ]
    available = [
        setup_tool,
        doctor_tool(),
        update_tool(),
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
            "name": "km_respond_candidate",
            "title": "Record Candidate Response",
            "description": "Record a contributor-safe user response: reminded, capture intent, snooze, or reject. This never approves or writes Wiki.",
            "inputSchema": object_schema({
                "candidate": {"type": "string"},
                "decision": {"type": "string", "enum": ["remind", "capture", "snooze", "reject"]},
                "responded_by": {"type": "string"},
                "reason": {"type": "string"},
                "until": {"type": "string", "description": "YYYY-MM-DD; required for snooze."},
                "dry_run": {"type": "boolean", "default": False},
            }, required=["candidate", "decision"]),
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
                "sensitivity": {"type": "string", "enum": ["normal", "sensitive"], "default": "normal"},
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


def doctor_tool() -> dict[str, Any]:
    return {
        "name": "km_doctor",
        "title": "Diagnose AgentsKM",
        "description": "Report plugin version, Profile, config, Vault health, and the next action.",
        "inputSchema": object_schema({}),
    }


def update_tool() -> dict[str, Any]:
    return {
        "name": "km_update",
        "title": "Update AgentsKM",
        "description": "Refresh AgentsKM from its configured GitHub marketplace or source checkout.",
        "inputSchema": object_schema({
            "check_only": {"type": "boolean", "default": False},
        }),
    }


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
    refresh_setup_status()
    if name == "km_setup_status":
        return cli_result(["setup-status", "--profile", PROFILE, "--json"])
    if name == "km_doctor":
        return cli_result(["doctor", "--profile", PROFILE, "--json"])
    if name == "km_update":
        update_host = "codex" if HOST == "codex" else "generic"
        update_args = ["update", "--host", update_host, "--json"]
        if bool(args.get("check_only", False)):
            update_args.append("--check")
        return cli_result(update_args)
    if name == "km_setup_instructions" and not SETUP_STATUS.get("configured"):
        payload = {
            **SETUP_STATUS,
            "ok": True,
            "write_via_mcp": False,
            "cli_path": str(KM),
            "next_step": (
                f'Run "{sys.executable}" "{KM}" setup --profile {PROFILE} '
                f"--host {HOST} --role contributor. The default Vault is created automatically."
            ),
        }
        return tool_payload(payload)
    if not SETUP_STATUS.get("configured"):
        raise ValueError("AgentsKM is in bootstrap mode; complete setup and restart the MCP server")
    mapping = {
        "km_status": ["status", "--json"],
        "km_pending": ["pending", "--json"],
        "km_reminders": ["reminders", "--json"],
        "km_validate": ["validate", "--json"],
        "km_lint": ["lint", "--json"],
    }
    if name in mapping:
        return cli_result(mapping[name])
    if name == "km_search":
        return cli_result(["search", require_string(args, "query"), "--limit", str(args.get("limit", 10)), "--json"])
    if name == "km_propose_capture":
        return cli_result(build_propose_args(args))
    if name == "km_respond_candidate":
        return cli_result(build_respond_args(args))
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
    command = cli_args[0]
    final_args = list(cli_args)
    runtime_commands = {
        "status", "pending", "reminders", "search", "validate", "lint", "propose",
        "respond", "review", "promote", "merge", "dashboard", "qmd-readiness",
    }
    if command in runtime_commands and "--profile" not in final_args:
        final_args.extend(["--profile", PROFILE])
    if CONFIG_PATH and "--config" not in final_args:
        final_args.extend(["--config", CONFIG_PATH])
    proc = subprocess.run(
        [sys.executable, str(KM), *final_args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    payload = parse_cli_json(proc.stdout, proc.stderr)
    is_error = proc.returncode != 0 or not bool(payload.get("ok", False))
    return tool_payload(payload, is_error=is_error)


def tool_payload(payload: dict[str, Any], is_error: bool = False) -> dict[str, Any]:
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
    data = dict(data)
    data.setdefault("agent_id", str(SETUP_STATUS.get("actor_id", PROFILE)))
    data.setdefault("source_tool", f"{SETUP_STATUS.get('host', HOST)}-mcp")
    data.setdefault("source_session", "unknown-session")
    args = [
        "propose",
        "--title", require_string(data, "title"),
        "--value-reason", require_string(data, "value_reason"),
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


def build_respond_args(data: dict[str, Any]) -> list[str]:
    data = dict(data)
    data.setdefault("agent_id", str(SETUP_STATUS.get("actor_id", PROFILE)))
    args = [
        "respond",
        require_string(data, "candidate"),
        "--decision", require_string(data, "decision"),
        "--json",
    ]
    append_option(args, data, "responded_by", "--responded-by")
    append_option(args, data, "agent_id", "--agent-id")
    append_option(args, data, "reason", "--reason")
    append_option(args, data, "until", "--until")
    if bool(data.get("dry_run", False)):
        args.append("--dry-run")
    return args


def build_promote_args(data: dict[str, Any]) -> list[str]:
    args = ["promote", require_string(data, "candidate"), "--json"]
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
        "--json",
    ]
    if bool(data.get("dry_run", False)):
        args.append("--dry-run")
    return args


def build_dashboard_args(data: dict[str, Any]) -> list[str]:
    args = ["dashboard", "--json"]
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


def load_setup_status(profile: str) -> dict[str, Any]:
    args = ["setup-status", "--profile", profile, "--json"]
    if CONFIG_PATH:
        args.extend(["--config", CONFIG_PATH])
    proc = subprocess.run(
        [sys.executable, str(KM), *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    payload = parse_cli_json(proc.stdout, proc.stderr)
    if proc.returncode != 0:
        return {
            "ok": False,
            "configured": False,
            "state": "setup_check_failed",
            "requested_profile": profile,
            "message": payload.get("error", "AgentsKM setup check failed"),
        }
    return payload


def refresh_setup_status() -> None:
    global SETUP_STATUS, ROLE
    SETUP_STATUS = load_setup_status(PROFILE)
    if SETUP_STATUS.get("configured"):
        ROLE = str(SETUP_STATUS["role"])


def bootstrap_profile(profile: str, host: str, role: str) -> None:
    args = [
        "setup",
        "--profile", profile,
        "--host", host,
        "--actor-id", profile,
        "--role", role,
        "--vault-name", "main",
        "--json",
    ]
    if role == "compiler":
        args.append("--confirm-compiler")
    if CONFIG_PATH:
        args.extend(["--config", CONFIG_PATH])
    proc = subprocess.run(
        [sys.executable, str(KM), *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    if proc.returncode != 0:
        return


if __name__ == "__main__":
    raise SystemExit(main())
