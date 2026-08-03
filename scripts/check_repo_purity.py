#!/usr/bin/env python3
"""Reject tracked runtime data, caches, build output, and obvious credentials."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = {
    ".agentskm",
    ".km",
    ".obsidian",
    ".pytest_cache",
    "000_Inbox",
    "__pycache__",
    "build",
    "dist",
    "raw",
}
FORBIDDEN_SUFFIXES = {".pyc", ".p12", ".pfx", ".pem", ".key"}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "PyPI token": re.compile(r"\bpypi-[A-Za-z0-9_-]{40,}\b"),
    "OpenAI key": re.compile(r"\bsk-[A-Za-z0-9_-]{32,}\b"),
}


def tracked_files() -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return [ROOT / item.decode("utf-8") for item in proc.stdout.split(b"\0") if item]


def main() -> int:
    issues: list[str] = []
    for path in tracked_files():
        rel = path.relative_to(ROOT)
        if any(part in FORBIDDEN_PARTS for part in rel.parts) or path.suffix in FORBIDDEN_SUFFIXES:
            issues.append(f"forbidden tracked path: {rel.as_posix()}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                issues.append(f"possible {label}: {rel.as_posix()}")
    if issues:
        print("Repository purity check failed:")
        print("\n".join(f"- {issue}" for issue in issues))
        return 1
    print("Repository purity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
