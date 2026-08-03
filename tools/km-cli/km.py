#!/usr/bin/env python3
"""Compatibility launcher for source checkouts.

The packaged implementation in ``src/agentskm_toolkit`` is the only runtime
source of truth. New integrations should invoke ``agentskm`` or
``python -m agentskm_toolkit`` instead of this file.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agentskm_toolkit.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
