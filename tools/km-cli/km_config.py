"""Compatibility imports for legacy source-checkout consumers."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agentskm_toolkit.km_config import *  # noqa: F403,E402
