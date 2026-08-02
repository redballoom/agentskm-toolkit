"""Productized console entry point for AgentsKM Toolkit."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence

from . import mcp
from .km import TOOLKIT_VERSION, emit_json, main as km_main


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if not args or args[0] in {"-h", "--help"}:
            print("usage: agentskm [--version] <command> [<args>]")
            print("")
            print("commands:")
            print("  mcp       start the stdio MCP server")
            print("  setup     create or extend AgentsKM config")
            print("  doctor    diagnose config, profile, and Vault")
            print("  search    search the configured Vault")
            print("  propose   create an Inbox candidate")
            print("  respond   record contributor-safe user response")
            print("  review    approve, snooze, or reject as reviewer+")
            print("  promote   promote approved candidate as compiler")
            print("  merge     merge approved candidate as compiler")
            print("")
            print("Use `agentskm <command> --help` for command-specific options.")
            return 0
        if args[0] in {"-V", "--version", "version"}:
            print(TOOLKIT_VERSION)
            return 0
        if args[0] == "mcp":
            return mcp.main(args[1:])
        return km_main(args)
    except (FileExistsError, FileNotFoundError, PermissionError, RuntimeError, ValueError) as exc:
        if "--json" in args:
            emit_json({"ok": False, "error": str(exc), "error_type": exc.__class__.__name__})
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())