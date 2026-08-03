#!/usr/bin/env python3
"""Validate the minimal AgentsKM Codex plugin assembly."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "agentskm-toolkit"
SKILL = PLUGIN / "skills" / "agentskm"
REQUIRED_FILES = (
    PLUGIN / ".codex-plugin" / "plugin.json",
    PLUGIN / ".mcp.json",
    SKILL / "SKILL.md",
    SKILL / "agents" / "openai.yaml",
    SKILL / "references" / "capture-workflow.md",
    SKILL / "references" / "setup-and-profiles.md",
    SKILL / "references" / "roles-and-approval.md",
)
FORBIDDEN_PATHS = (
    PLUGIN / "README.md",
    PLUGIN / "tools",
    PLUGIN / "adapters",
    PLUGIN / "vault",
    PLUGIN / "config.json",
    PLUGIN / "skills" / "agentskm-capture",
)


def skill_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError("Skill must start with YAML frontmatter")
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            raise ValueError(f"Invalid Skill frontmatter line: {line}")
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip()
    return result


def validate_manifest() -> list[str]:
    issues: list[str] = []
    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if manifest.get("name") != PLUGIN.name:
        issues.append("plugin name must match its directory")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", str(manifest.get("version", ""))):
        issues.append("plugin version must be strict semver")
    if manifest.get("skills") != "./skills/":
        issues.append("plugin skills path must be ./skills/")
    if manifest.get("mcpServers") != "./.mcp.json":
        issues.append("plugin MCP path must be ./.mcp.json")
    if "hooks" in manifest or "apps" in manifest:
        issues.append("plugin declares an unsupported or absent companion component")
    prompts = manifest.get("interface", {}).get("defaultPrompt", [])
    if not isinstance(prompts, list) or len(prompts) > 1:
        issues.append("plugin must expose at most one domain-level starter prompt")
    return issues


def validate_skill() -> list[str]:
    issues: list[str] = []
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill_frontmatter(text)
    if set(frontmatter) != {"name", "description"}:
        issues.append("Skill frontmatter must contain only name and description")
    if frontmatter.get("name") != SKILL.name:
        issues.append("Skill name must match its directory")
    if not frontmatter.get("description"):
        issues.append("Skill description must be non-empty")
    if len(text.splitlines()) > 100:
        issues.append("Skill body exceeds the 100-line product target")
    for reference in ("capture-workflow.md", "setup-and-profiles.md", "roles-and-approval.md"):
        if f"references/{reference}" not in text:
            issues.append(f"Skill does not directly reference {reference}")
    metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if "$agentskm" not in metadata:
        issues.append("openai.yaml default prompt must mention $agentskm")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Validation is always read-only")
    parser.add_argument("--skip-uvx-check", action="store_true", help="Skip the host uvx prerequisite check")
    args = parser.parse_args()

    issues: list[str] = []
    for path in REQUIRED_FILES:
        if not path.is_file():
            issues.append(f"missing: {path.relative_to(ROOT).as_posix()}")
    for path in FORBIDDEN_PATHS:
        if path.exists():
            issues.append(f"forbidden: {path.relative_to(ROOT).as_posix()}")
    for path in PLUGIN.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".pyc"}:
            issues.append(f"runtime source in plugin: {path.relative_to(ROOT).as_posix()}")

    if not issues:
        issues.extend(validate_manifest())
        issues.extend(validate_skill())
        server = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["agentskm"]
        if server.get("command") != "uvx":
            issues.append("plugin MCP command must be uvx")
        if server.get("args", [])[:1] != ["--from"]:
            issues.append("plugin MCP runtime must begin with uvx --from")
    if not args.skip_uvx_check and shutil.which("uvx") is None:
        issues.append("uvx is required on the host PATH")

    if issues:
        print("Plugin validation failed:")
        print("\n".join(f"- {issue}" for issue in issues))
        return 1
    print("Minimal plugin assembly is valid; runtime is provided by the pinned PyPI package through uvx.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
