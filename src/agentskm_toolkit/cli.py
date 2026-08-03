"""Productized console entry point for AgentsKM Toolkit."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence

from . import mcp
from .km import TOOLKIT_VERSION, emit_json, error_payload, main as km_main


COMMANDS = (
    ("setup-status", "check configuration and Profile readiness"),
    ("setup", "create or extend AgentsKM configuration"),
    ("doctor", "diagnose config, Profile, role, Vault, and locks"),
    ("status", "show Vault counts by layer"),
    ("search", "search Wiki, Inbox, Raw, and docs"),
    ("pending", "list active Inbox candidates"),
    ("reminders", "list new and due candidates"),
    ("validate", "validate required frontmatter"),
    ("lint", "check wikilinks and misplaced pages"),
    ("propose", "create an Inbox candidate"),
    ("respond", "record a contributor-safe response"),
    ("review", "review a candidate as reviewer or compiler"),
    ("promote", "promote an approved candidate as compiler"),
    ("merge", "merge an approved candidate as compiler"),
    ("dashboard", "generate the review dashboard"),
    ("qmd-readiness", "generate the optional qmd readiness report"),
    ("update", "check or refresh the installed toolkit"),
    ("mcp", "start the stdio MCP server"),
)


def print_help() -> None:
    print("usage: agentskm [--version] <command> [<args>]")
    print("\nManage a local multi-agent knowledge Vault.")
    print("\ncommands:")
    width = max(len(name) for name, _ in COMMANDS)
    for name, description in COMMANDS:
        print(f"  {name:<{width}}  {description}")
    print("\nUse `agentskm <command> --help` for command-specific options and defaults.")
    print("Exit codes: 0 success; 1 health/validation issues; 2 input, configuration, permission, or runtime failure.")


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args or args[0] in {"-h", "--help"}:
            print_help()
            return 0
        if args[0] in {"-V", "--version", "version"}:
            print(TOOLKIT_VERSION)
            return 0
        if args[0] == "mcp":
            return mcp.main(args[1:])
        return km_main(args)
    except (FileExistsError, FileNotFoundError, PermissionError, RuntimeError, ValueError) as exc:
        if "--json" in args:
            emit_json(error_payload(exc))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
