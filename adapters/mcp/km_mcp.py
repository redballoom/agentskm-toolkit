#!/usr/bin/env python3
"""Compatibility launcher for the packaged AgentsKM MCP server."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agentskm_toolkit.mcp import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
