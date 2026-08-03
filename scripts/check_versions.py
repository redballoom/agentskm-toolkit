#!/usr/bin/env python3
"""Check that every distributable AgentsKM surface reports one version."""

from __future__ import annotations

import ast
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "agentskm_toolkit"
MANIFEST = ROOT / "plugins" / "agentskm-toolkit" / ".codex-plugin" / "plugin.json"
MCP_CONFIG = ROOT / "plugins" / "agentskm-toolkit" / ".mcp.json"


def assigned_string(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        return node.value.value
    raise RuntimeError(f"{path}: string assignment not found: {name}")


def project_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    project = re.search(r"(?ms)^\[project\]\s*(.*?)(?=^\[|\Z)", text)
    if not project:
        raise RuntimeError(f"{path}: [project] table not found")
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', project.group(1))
    if not match:
        raise RuntimeError(f"{path}: project.version not found")
    return match.group(1)


def run_source(args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "agentskm_toolkit", *args],
        cwd=ROOT,
        env=env,
        input=input_text,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--simulate-mismatch",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    declared_version = project_version(ROOT / "pyproject.toml")
    package_version = assigned_string(PACKAGE / "__init__.py", "__version__")
    plugin_version = json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]
    server = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))["mcpServers"]["agentskm"]
    package_arg = server["args"][server["args"].index("--from") + 1]
    pin_match = re.fullmatch(r"agentskm-toolkit==(.+)", package_arg)
    if not pin_match:
        raise RuntimeError(f"Plugin MCP runtime must use an exact package pin: {package_arg}")

    cli = run_source(["--version"])
    if cli.returncode != 0:
        raise RuntimeError(cli.stderr or cli.stdout)
    cli_version = cli.stdout.strip()

    with tempfile.TemporaryDirectory(prefix="agentskm-version-") as temp:
        config = Path(temp) / "config.json"
        messages = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) + "\n"
        mcp = run_source([
            "mcp", "--profile", "version-check", "--host", "generic",
            "--bootstrap-role", "contributor", "--config", str(config),
        ], input_text=messages)
    if mcp.returncode != 0:
        raise RuntimeError(mcp.stderr or mcp.stdout)
    response = json.loads(next(line for line in mcp.stdout.splitlines() if line.strip()))
    mcp_version = response["result"]["serverInfo"]["version"]

    versions = {
        "pyproject": declared_version,
        "package": package_version,
        "cli": cli_version,
        "mcp": mcp_version,
        "plugin": plugin_version,
        "plugin_pin": pin_match.group(1),
    }
    if args.simulate_mismatch:
        versions["plugin"] = "0.0.0-simulated-mismatch"
    if len(set(versions.values())) != 1:
        print(json.dumps({"ok": False, "versions": versions}, indent=2))
        return 1
    print(json.dumps({"ok": True, "version": declared_version, "versions": versions}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
