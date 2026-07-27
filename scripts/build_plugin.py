#!/usr/bin/env python3
"""Build or verify the self-contained AgentsKM plugin package."""

from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "agentskm-toolkit"
COPIES = {
    ROOT / "tools" / "km-cli" / "km.py": PLUGIN / "tools" / "km-cli" / "km.py",
    ROOT / "tools" / "km-cli" / "README.md": PLUGIN / "tools" / "km-cli" / "README.md",
    ROOT / "adapters" / "mcp" / "km_mcp.py": PLUGIN / "adapters" / "mcp" / "km_mcp.py",
    ROOT / "adapters" / "mcp" / "README.md": PLUGIN / "adapters" / "mcp" / "README.md",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    stale: list[str] = []
    for source, target in COPIES.items():
        if args.check:
            if not target.exists() or not filecmp.cmp(source, target, shallow=False):
                stale.append(target.relative_to(ROOT).as_posix())
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    if stale:
        print("Plugin runtime is stale:")
        for path in stale:
            print(f"- {path}")
        return 1
    print("Plugin runtime is synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
