#!/usr/bin/env python3
"""Render an AgentsKM MCP configuration for agent hosts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MCP = ROOT / "adapters" / "mcp" / "km_mcp.py"


def server_config(args: argparse.Namespace) -> dict[str, object]:
    common_args = [
        "--profile", args.profile,
        "--host", args.agent,
        "--bootstrap-role", args.role,
    ]
    if args.config:
        common_args.extend(["--config", str(Path(args.config).expanduser().resolve())])

    if args.runtime == "source":
        return {
            "command": "python",
            "args": [str(MCP), *common_args],
        }
    if args.runtime == "agentskm":
        return {
            "command": args.agentskm_command,
            "args": ["mcp", *common_args],
        }
    return {
        "command": args.uvx_command,
        "args": ["--from", args.package, args.agentskm_command, "mcp", *common_args],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", choices=["claude", "cursor", "hermes", "codex", "generic"], required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--role", choices=["contributor", "reviewer", "compiler"], default="contributor")
    parser.add_argument("--runtime", choices=["uvx", "agentskm", "source"], default="uvx")
    parser.add_argument("--package", default="agentskm-toolkit")
    parser.add_argument("--uvx-command", default="uvx")
    parser.add_argument("--agentskm-command", default="agentskm")
    parser.add_argument("--config")
    parser.add_argument("--output")
    args = parser.parse_args()

    config = {"mcpServers": {"agentskm": server_config(args)}}
    text = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8", newline="\n")
        print(f"Wrote {args.agent} MCP config: {output}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
