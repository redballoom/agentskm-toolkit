#!/usr/bin/env python3
"""Render an AgentsKM MCP configuration for non-Codex agent hosts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MCP = ROOT / "adapters" / "mcp" / "km_mcp.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", choices=["claude", "cursor", "hermes", "generic"], required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--config")
    parser.add_argument("--output")
    args = parser.parse_args()

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["AGENTSKM_PROFILE"] = args.profile
    if args.config:
        env["AGENTSKM_CONFIG"] = str(Path(args.config).expanduser().resolve())
    status = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "km-cli" / "km.py"), "setup-status", "--profile", args.profile, "--json"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        env=env,
        capture_output=True,
    )
    if status.returncode != 0:
        parser.error(status.stderr or status.stdout or "AgentsKM setup check failed")
    payload = json.loads(status.stdout)
    if not payload.get("configured"):
        parser.error(f"Profile is not ready: {args.profile} ({payload.get('state')})")

    config = {
        "mcpServers": {
            "agentskm": {
                "command": "python",
                "args": [str(MCP), "--profile", args.profile],
                "env": {
                    "AGENTSKM_PROFILE": args.profile,
                    "PYTHONUTF8": "1",
                },
            }
        }
    }
    if args.config:
        config["mcpServers"]["agentskm"]["env"]["AGENTSKM_CONFIG"] = env["AGENTSKM_CONFIG"]
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
