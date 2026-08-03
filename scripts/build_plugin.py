#!/usr/bin/env python3
"""Verify the lightweight AgentsKM Codex plugin package."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "agentskm-toolkit"
REQUIRED_PATHS = (
    PLUGIN / ".codex-plugin" / "plugin.json",
    PLUGIN / ".mcp.json",
    PLUGIN / "README.md",
    PLUGIN / "commands" / "km-doctor.md",
    PLUGIN / "commands" / "km-capture.md",
    PLUGIN / "commands" / "km-search.md",
    PLUGIN / "skills" / "agentskm-capture" / "SKILL.md",
)
FORBIDDEN_PATHS = (
    PLUGIN / "adapters",
    PLUGIN / "tools",
    PLUGIN / "commands" / "README.md",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Retained for workflow compatibility; validation is always read-only.",
    )
    parser.parse_args()

    missing = [path for path in REQUIRED_PATHS if not path.is_file()]
    forbidden = [path for path in FORBIDDEN_PATHS if path.exists()]
    if missing or forbidden:
        if missing:
            print("Plugin files are missing:")
            for path in missing:
                print(f"- {path.relative_to(ROOT).as_posix()}")
        if forbidden:
            print("Plugin contains forbidden paths:")
            for path in forbidden:
                print(f"- {path.relative_to(ROOT).as_posix()}")
        return 1

    print("Lightweight plugin package is valid; runtime is provided by PyPI through uvx.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
