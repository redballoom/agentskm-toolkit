#!/usr/bin/env python3
"""Build an ignored local Codex marketplace backed by the current wheel."""

from __future__ import annotations

import json
import shutil
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SOURCE = ROOT / "plugins" / "agentskm-toolkit"
OUTPUT = ROOT / "build" / "local-codex-marketplace"


def project_version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return str(tomllib.load(handle)["project"]["version"])


def main() -> int:
    version = project_version()
    wheels = sorted((ROOT / "dist").glob(f"agentskm_toolkit-{version}-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(
            f"Expected one dist wheel for {version}; run `python -m build` first"
        )
    wheel = wheels[0].resolve()

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    plugin_output = OUTPUT / "plugins" / "agentskm-toolkit"
    shutil.copytree(PLUGIN_SOURCE, plugin_output)

    mcp_path = plugin_output / ".mcp.json"
    mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
    args = mcp["mcpServers"]["agentskm"]["args"]
    args[args.index("--from") + 1] = str(wheel)
    mcp_path.write_text(json.dumps(mcp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    marketplace = {
        "name": "agentskm-local",
        "interface": {"displayName": "AgentsKM Local Test"},
        "plugins": [
            {
                "name": "agentskm-toolkit",
                "source": {"source": "local", "path": "./plugins/agentskm-toolkit"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity",
            }
        ],
    }
    manifest = OUTPUT / ".agents" / "plugins" / "marketplace.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(marketplace, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": True,
        "version": version,
        "marketplace": str(OUTPUT),
        "plugin": str(plugin_output),
        "runtime_wheel": str(wheel),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
