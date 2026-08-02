#!/usr/bin/env python3
"""Local KM CLI for AgentsKM.

The CLI is deliberately small and deterministic. It is the only supported path
for multi-agent writes once adapters are added.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

try:
    from .km_config import (
        DEFAULT_VAULT,
        RuntimeContext,
        default_config,
        get_config_path,
        inspect_setup,
        is_legacy_config,
        read_json,
        resolve_runtime,
        validate_config,
        vault_is_valid,
    )
except ImportError:
    from km_config import (
        DEFAULT_VAULT,
        RuntimeContext,
        default_config,
        get_config_path,
        inspect_setup,
        is_legacy_config,
        read_json,
        resolve_runtime,
        validate_config,
        vault_is_valid,
    )

TOOLKIT_VERSION = "0.4.4"
TOOLKIT_REPOSITORY = "https://github.com/redballoom/agentskm-toolkit"
CODEX_MARKETPLACE = "agentskm-local"
CODEX_PLUGIN = "agentskm-toolkit"
TOOL_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = get_config_path()
ROOT = TOOL_ROOT
KM_DIR = ROOT / ".km"
LOCK_DIR = KM_DIR / "locks"
TX_DIR = KM_DIR / "transactions"
RUNTIME: RuntimeContext | None = None
SKIP_DIRS = {".git", ".obsidian", ".learnings", ".km"}
WIKI_DIRS = {
    "entity": "wiki/entities",
    "concept": "wiki/concepts",
    "comparison": "wiki/comparisons",
    "query": "wiki/queries",
    "guide": "wiki/queries",
    "note": "wiki/concepts",
    "summary": "wiki/concepts",
}
WIKI_SECTION = {
    "entity": "Entities",
    "concept": "Concepts",
    "comparison": "Comparisons",
    "query": "Queries",
    "guide": "Queries",
    "note": "Concepts",
    "summary": "Concepts",
}
WIKI_REQUIRED = {"title", "created", "updated", "type", "tags", "source_refs"}
INBOX_REQUIRED = {"title", "created", "updated", "status", "type", "tags", "confidence"}
TERMINAL_INBOX = {"graduated", "merged", "rejected"}
ACTIVE_INBOX = {
    "pending",
    "pending-source-review",
    "reminded",
    "snoozed",
    "approved",
    "duplicate",
}
ROLE_ORDER = {"contributor": 1, "reviewer": 2, "compiler": 3}
EXAMPLE_WIKILINKS = {
    "excel-to-web-form-automation",
    "shadow-dom-element-scraping",
    "wikilinks",
}
LINT_REFERENCE_DOCS = {
    "docs/AgentsKM-P0-基线盘点报告.md",
}
QMD_READINESS_QUERIES = [
    "领星 API 怎么鉴权",
    "WSL 如何连接 Windows Chrome CDP",
    "Docsify API 提取方法论",
]
QUERY_STOPWORDS = {
    "怎么", "如何", "怎样", "请问", "请", "一下", "什么", "为什么", "是否",
    "可以", "能否", "如何连接", "怎么连接",
}


@dataclass
class Page:
    path: Path
    rel: str
    text: str
    meta: dict[str, str]

    @property
    def title(self) -> str:
        if self.meta.get("title"):
            return self.meta["title"]
        for line in self.text.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return self.path.stem

    @property
    def status(self) -> str:
        return self.meta.get("status", "")

    @property
    def layer(self) -> str:
        if self.rel.startswith("wiki/"):
            return "wiki"
        if self.rel.startswith("000_Inbox/"):
            return "inbox"
        if self.rel.startswith("raw/"):
            return "raw"
        if self.rel.startswith("docs/"):
            return "docs"
        if self.rel.startswith("tools/"):
            return "tools"
        return "root"


def page_summary(page: Page, snippet: str | None = None) -> dict[str, object]:
    data: dict[str, object] = {
        "path": page.rel,
        "layer": page.layer,
        "title": page.title,
        "status": page.status,
        "type": page.meta.get("type", ""),
        "tags": meta_list(page.meta, "tags"),
        "source_refs": meta_list(page.meta, "source_refs"),
    }
    if snippet is not None:
        data["snippet"] = snippet
    suggested_target = page.meta.get("suggested_target", "")
    if suggested_target:
        data["suggested_target"] = suggested_target
    return data


def emit_json(data: dict[str, object]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def wants_json(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "json", False))


def ensure_vault_root() -> None:
    required = [ROOT / "000_Inbox", ROOT / "wiki"]
    if all(path.is_dir() for path in required):
        return
    raise RuntimeError(
        "AgentsKM vault is not configured. Run `km setup-status --json`, then "
        "complete `km setup`."
    )


def actor_role(args: argparse.Namespace) -> str:
    role = (RUNTIME.role if RUNTIME else None) or "contributor"
    if role not in ROLE_ORDER:
        raise ValueError(f"Unknown actor role: {role}")
    return role


def activate_runtime(context: RuntimeContext) -> None:
    global ROOT, KM_DIR, LOCK_DIR, TX_DIR, RUNTIME
    RUNTIME = context
    ROOT = context.vault_path
    KM_DIR = ROOT / ".km"
    LOCK_DIR = KM_DIR / "locks"
    TX_DIR = KM_DIR / "transactions"


def require_role(args: argparse.Namespace, minimum: str, action: str) -> str:
    role = actor_role(args)
    if ROLE_ORDER[role] < ROLE_ORDER[minimum]:
        raise PermissionError(f"{action} requires role={minimum}; current role={role}")
    return role


def require_approval(args: argparse.Namespace) -> None:
    if not getattr(args, "approved_by", "").strip():
        raise ValueError("Explicit --approved-by is required")
    if not getattr(args, "scope", "").strip():
        raise ValueError("Explicit --scope is required")


class RepoLock:
    def __init__(self, name: str = "repo", timeout: float = 10.0) -> None:
        self.path = LOCK_DIR / f"{name}.lock"
        self.timeout = timeout
        self.fd: int | None = None

    def __enter__(self) -> "RepoLock":
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        while True:
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                payload = f"pid={os.getpid()} created={datetime.now().isoformat(timespec='seconds')}\n"
                os.write(self.fd, payload.encode("utf-8"))
                return self
            except FileExistsError:
                if time.monotonic() - start >= self.timeout:
                    raise RuntimeError(f"Could not acquire lock: {self.path}")
                time.sleep(0.2)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


class Transaction:
    def __init__(self, name: str) -> None:
        self.id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.getpid()}-{name}"
        self.dir = TX_DIR / self.id
        self.backups = self.dir / "backups"
        self.touched: set[Path] = set()

    def __enter__(self) -> "Transaction":
        self.backups.mkdir(parents=True, exist_ok=False)
        return self

    def backup(self, path: Path) -> None:
        path = path.resolve()
        if path in self.touched:
            return
        self.touched.add(path)
        if path.exists():
            rel = path.relative_to(ROOT)
            backup_path = self.backups / rel
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_path)

    def write_text(self, path: Path, text: str) -> None:
        path = resolve_repo_path(path)
        self.backup(path)
        atomic_write(path, text)

    def __exit__(self, exc_type, exc, tb) -> None:
        rollback_errors: list[str] = []
        if exc_type:
            rollback_errors = self.rollback()
        status = {
            "id": self.id,
            "finished_at": datetime.now().isoformat(timespec="seconds"),
            "status": "failed" if exc_type else "committed",
            "touched": [p.relative_to(ROOT).as_posix() for p in sorted(self.touched)],
            "rollback_errors": rollback_errors,
        }
        (self.dir / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

    def rollback(self) -> list[str]:
        errors: list[str] = []
        for path in sorted(self.touched, reverse=True):
            try:
                rel = path.relative_to(ROOT)
                backup_path = self.backups / rel
                if backup_path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_path, path)
                elif path.exists():
                    path.unlink()
            except OSError as exc:
                errors.append(f"{path.relative_to(ROOT).as_posix()}: {exc}")
        return errors


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temp, path)


def initialize_empty_vault(path: Path) -> bool:
    """Create the minimal, human-readable Vault layout used on first install."""
    if vault_is_valid(path):
        return False
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"Refusing to initialize a non-empty non-AgentsKM directory: {path}")
    for relative in (
        "000_Inbox",
        "wiki/entities",
        "wiki/concepts",
        "wiki/comparisons",
        "wiki/queries",
        "raw",
        "docs",
    ):
        (path / relative).mkdir(parents=True, exist_ok=True)
    atomic_write(
        path / "README.md",
        "# AgentsKM Vault\n\n"
        "This directory contains private knowledge data managed by AgentsKM.\n\n"
        "- `000_Inbox/`: unreviewed candidates from all connected Agents\n"
        "- `wiki/`: reviewed, durable knowledge\n"
        "- `raw/`: source evidence retained when needed\n"
        "- `docs/`: Vault-local operating notes and dashboards\n\n"
        "Change the Vault path in `%USERPROFILE%/.agentskm/config.json` to bind "
        "all configured Agent Profiles to another local Vault.\n",
    )
    atomic_write(
        path / "index.md",
        "# AgentsKM\n\n"
        "## Entities\n\n"
        "## Concepts\n\n"
        "## Comparisons\n\n"
        "## Queries\n",
    )
    return True


class ConfigLock:
    def __init__(self, timeout: float = 10.0) -> None:
        self.path = CONFIG_PATH.with_suffix(CONFIG_PATH.suffix + ".lock")
        self.timeout = timeout
        self.fd: int | None = None

    def __enter__(self) -> "ConfigLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        started = time.monotonic()
        while True:
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, f"pid={os.getpid()}\n".encode("utf-8"))
                return self
            except FileExistsError:
                if time.monotonic() - started >= self.timeout:
                    raise RuntimeError(f"Could not acquire config lock: {self.path}")
                time.sleep(0.2)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def resolve_repo_path(path: Path | str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    resolved = candidate.resolve()
    root = ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"Path is outside repository: {path}")
    return resolved


def iter_markdown() -> list[Page]:
    pages: list[Page] = []
    for path in ROOT.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        pages.append(Page(path=path, rel=rel, text=text, meta=parse_frontmatter(text)))
    return sorted(pages, key=lambda page: page.rel)


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}
    meta: dict[str, str] = {}
    current_key = ""
    for raw_line in match.group(1).splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if re.match(r"^[A-Za-z_][A-Za-z0-9_-]*:", line):
            key, value = line.split(":", 1)
            current_key = key.strip()
            meta[current_key] = parse_meta_scalar(value.strip())
        elif current_key and line.lstrip().startswith("- "):
            prior = meta.get(current_key, "")
            item = parse_meta_scalar(line.strip()[2:].strip())
            meta[current_key] = f"{prior}, {item}".strip(", ")
    return meta


def parse_meta_scalar(value: str) -> str:
    if not value:
        return ""
    try:
        decoded = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value
    if isinstance(decoded, (dict, list)):
        return value
    if decoded is None:
        return ""
    if isinstance(decoded, bool):
        return "true" if decoded else "false"
    return str(decoded)


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    match = re.match(r"---\n(.*?)\n---\n?", text, re.DOTALL)
    if not match:
        return {}, text
    return parse_frontmatter(text), text[match.end():]


def render_page(meta: dict[str, object], body: str) -> str:
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, list):
            serialized = json.dumps([str(item) for item in value], ensure_ascii=False)
            lines.append(f"{key}: {serialized}")
        else:
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body.lstrip()


def meta_list(meta: dict[str, str], key: str) -> list[str]:
    value = meta.get(key, "").strip()
    if not value:
        return []
    if value.startswith("[") and value.endswith("]"):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            value = value[1:-1]
        else:
            if isinstance(decoded, list):
                return [str(item) for item in decoded if str(item).strip()]
    return [item.strip().strip("'\"") for item in value.split(",") if item.strip()]


def today() -> str:
    return date.today().isoformat()


def slugify(value: str) -> str:
    raw = value.casefold().strip()
    raw = re.sub(r"[^a-z0-9]+", "-", raw)
    return raw.strip("-")


def normalize_for_fingerprint(*parts: object) -> str:
    text = "\n".join(str(part) for part in parts if part is not None)
    return re.sub(r"\s+", " ", text.casefold()).strip()


def fingerprint(*parts: object) -> str:
    return hashlib.sha256(normalize_for_fingerprint(*parts).encode("utf-8")).hexdigest()


def next_candidate_id() -> str:
    prefix = f"kmc-{today().replace('-', '')}-"
    max_seq = 0
    for page in iter_markdown():
        candidate_id = page.meta.get("id", "")
        if candidate_id.startswith(prefix):
            try:
                max_seq = max(max_seq, int(candidate_id.rsplit("-", 1)[1]))
            except ValueError:
                continue
    return f"{prefix}{max_seq + 1:04d}"


def find_page_by_rel(rel: str) -> Page | None:
    rel = rel.replace("\\", "/").strip("/")
    for page in iter_markdown():
        if page.rel == rel:
            return page
    return None


def command_status(args: argparse.Namespace) -> int:
    pages = iter_markdown()
    layers = {"wiki": 0, "inbox": 0, "raw": 0, "docs": 0, "tools": 0, "root": 0}
    for page in pages:
        layers[page.layer] += 1
    data = {
        "ok": True,
        "runtime": RUNTIME.as_dict() if RUNTIME else None,
        "layers": layers,
        "total_markdown": len(pages),
    }
    if wants_json(args):
        emit_json(data)
        return 0
    print("AgentsKM status")
    for key in ("wiki", "inbox", "raw", "docs", "tools", "root"):
        print(f"- {key}: {layers[key]}")
    print(f"- total markdown: {len(pages)}")
    return 0


def command_pending(args: argparse.Namespace) -> int:
    pages = [page for page in iter_markdown() if page.layer == "inbox"]
    active = [
        page for page in pages
        if page.status not in TERMINAL_INBOX
    ]
    items = [page_summary(page) for page in active]
    if wants_json(args):
        emit_json({"ok": True, "count": len(items), "candidates": items})
        return 0
    if not active:
        print("No pending inbox candidates.")
        return 0
    for page in active:
        status = page.status or "unknown"
        target = page.meta.get("suggested_target", "")
        suffix = f" -> {target}" if target else ""
        print(f"{status}: {page.rel} | {page.title}{suffix}")
    return 0


def command_search(args: argparse.Namespace) -> int:
    payload, raw_matches = search_pages(args.query, limit=args.limit)
    if wants_json(args):
        emit_json(payload)
        return 0
    for _, page, snippet in raw_matches:
        status = f" status={page.status}" if page.status else ""
        print(f"[{page.layer}]{status} {page.rel} | {page.title}")
        print(f"  {snippet}")
    if not raw_matches:
        print("No matches.")
    return 0


def compact_snippet(text: str, idx: int, width: int) -> str:
    start = max(0, idx - 45)
    end = min(len(text), idx + width + 70)
    snippet = text[start:end].replace("\n", " ")
    return re.sub(r"\s+", " ", snippet).strip()


def command_validate(args: argparse.Namespace) -> int:
    issues: list[str] = []
    for page in iter_markdown():
        if page.layer == "wiki":
            missing = sorted(WIKI_REQUIRED - page.meta.keys())
            if missing:
                issues.append(f"{page.rel}: missing wiki frontmatter fields: {', '.join(missing)}")
            if page.meta.get("status") not in {"active", "draft", "archived"}:
                issues.append(f"{page.rel}: wiki status must be active, draft, or archived")
        if page.layer == "inbox":
            missing = sorted(INBOX_REQUIRED - page.meta.keys())
            if missing:
                issues.append(f"{page.rel}: missing inbox frontmatter fields: {', '.join(missing)}")
            if page.status not in ACTIVE_INBOX | TERMINAL_INBOX:
                issues.append(f"{page.rel}: unknown inbox status: {page.status}")
            if page.status not in {"pending-source-review", "rejected"} and not page.meta.get("source_refs"):
                issues.append(f"{page.rel}: source_refs is required unless pending-source-review")
    if issues:
        if wants_json(args):
            emit_json({"ok": False, "issues": issues})
            return 1
        print("\n".join(issues))
        return 1
    if wants_json(args):
        emit_json({"ok": True, "issues": []})
        return 0
    print("Validation passed.")
    return 0


def command_lint(args: argparse.Namespace) -> int:
    pages = iter_markdown()
    known = build_known_targets(pages)
    issues: list[str] = []
    for page in pages:
        if page.rel in LINT_REFERENCE_DOCS:
            continue
        for target in re.findall(r"\[\[([^\]|#]+)", page.text):
            normalized = normalize_target(target)
            if page.rel in {"purpose.md", "SCHEMA.md", "docs/AgentsKM-架构改造执行计划.md"} and normalized in EXAMPLE_WIKILINKS:
                continue
            if normalized not in known:
                issues.append(f"{page.rel}: broken wikilink [[{target}]]")
    root_concepts = ROOT / "concepts"
    if root_concepts.exists():
        leftovers = list(root_concepts.rglob("*.md"))
        for path in leftovers:
            rel = path.relative_to(ROOT).as_posix()
            issues.append(f"{rel}: formal page remains outside wiki/")
    if issues:
        if wants_json(args):
            emit_json({"ok": False, "issues": issues})
            return 1
        print("\n".join(issues))
        return 1
    if wants_json(args):
        emit_json({"ok": True, "issues": []})
        return 0
    print("Lint passed.")
    return 0


def build_known_targets(pages: list[Page]) -> set[str]:
    known: set[str] = set()
    for page in pages:
        rel_no_ext = page.rel[:-3] if page.rel.endswith(".md") else page.rel
        known.add(rel_no_ext.casefold())
        known.add(Path(rel_no_ext).name.casefold())
        if page.layer == "wiki":
            known.add(page.path.stem.casefold())
    return known


def normalize_target(target: str) -> str:
    target = target.strip().replace("\\", "/")
    if target.endswith(".md"):
        target = target[:-3]
    return target.casefold()


def command_propose(args: argparse.Namespace) -> int:
    role = require_role(args, "contributor", "propose")
    if args.sensitivity == "secret":
        raise ValueError("Refusing to persist a candidate with sensitivity=secret")
    source_refs = default_source_refs(args.source_ref or [], args.source_session)
    tags = unique(["implicit-capture", *parse_csv(args.tags)])
    body = load_body(args.body, args.body_file, args.title, args.value_reason)
    candidate_id = next_candidate_id()
    candidate_fingerprint = fingerprint(args.title, body, args.value_reason)

    duplicate = find_duplicate_candidate(
        candidate_fingerprint,
        args.title,
        args.suggested_target,
    )
    if duplicate:
        updated = update_duplicate_candidate(duplicate, args, source_refs, dry_run=args.dry_run)
        if wants_json(args):
            emit_json({
                "ok": True,
                "duplicate": True,
                "updated": updated,
                "candidate": page_summary(duplicate),
                "fingerprint": candidate_fingerprint,
            })
            return 0
        print(f"Duplicate candidate fingerprint: {duplicate.rel}")
        return 0

    slug = slugify(args.slug or args.title) or candidate_id
    target_path = ROOT / "000_Inbox" / f"{slug}.md"
    if target_path.exists():
        target_path = ROOT / "000_Inbox" / f"{slug}-{candidate_id}.md"

    status = "pending" if source_refs else "pending-source-review"
    meta: dict[str, object] = {
        "id": candidate_id,
        "title": args.title,
        "created": today(),
        "updated": today(),
        "status": status,
        "type": args.type,
        "tags": tags,
        "agent_id": args.agent_id,
        "source_tool": args.source_tool,
        "source_session": args.source_session,
        "contributor_agents": [args.agent_id],
        "source_sessions": [args.source_session],
        "source_refs": source_refs,
        "suggested_action": args.suggested_action,
        "suggested_target": args.suggested_target,
        "value_reason": args.value_reason,
        "confidence": args.confidence,
        "sensitivity": args.sensitivity,
        "fingerprint": candidate_fingerprint,
    }
    content = render_page(meta, body)
    rel = target_path.relative_to(ROOT).as_posix()
    if args.dry_run:
        if wants_json(args):
            emit_json({
                "ok": True,
                "dry_run": True,
                "candidate_path": rel,
                "candidate": meta,
                "content": content,
            })
            return 0
        print(f"DRY RUN propose -> {rel}")
        print(content)
        return 0

    with RepoLock(timeout=args.lock_timeout), Transaction("propose") as tx:
        tx.write_text(target_path, content)
        append_log(tx, "propose", args.title, [
            f"candidate: {rel}",
            f"status: {status}",
            f"suggested_target: {args.suggested_target or '(none)'}",
            f"agent_id: {args.agent_id}",
            f"actor_role: {role}",
        ])
    if wants_json(args):
        emit_json({
            "ok": True,
            "created": True,
            "candidate_path": rel,
            "status": status,
            "fingerprint": candidate_fingerprint,
        })
        return 0
    print(f"Created candidate: {rel}")
    return 0


def default_source_refs(source_refs: list[str], source_session: str) -> list[str]:
    refs = [item for item in source_refs if item]
    session = (source_session or "").strip()
    if refs or not session or session in {"manual", "unknown-session"}:
        return refs
    return [f"conversation:{session}"]


def command_reminders(args: argparse.Namespace) -> int:
    due: list[Page] = []
    today_value = today()
    for page in iter_markdown():
        if page.layer != "inbox":
            continue
        if page.status in {"pending", "pending-source-review"}:
            due.append(page)
        elif page.status == "snoozed" and page.meta.get("snoozed_until", "") <= today_value:
            due.append(page)
    items = [page_summary(page) for page in due]
    if wants_json(args):
        emit_json({"ok": True, "count": len(items), "candidates": items})
        return 0
    if not items:
        print("No knowledge reminders are due.")
        return 0
    for page in due:
        print(f"{page.status}: {page.rel} | {page.title}")
    return 0


def command_review(args: argparse.Namespace) -> int:
    role = require_role(args, "reviewer", "review")
    candidate = load_candidate(args.candidate)
    if candidate.status in TERMINAL_INBOX:
        raise ValueError(f"Candidate is already terminal: {candidate.status}")

    decision = args.decision
    if decision == "approve":
        if candidate.meta.get("sensitivity") == "secret":
            raise ValueError("Refusing to approve candidate with sensitivity=secret")
        if not meta_list(candidate.meta, "source_refs"):
            raise ValueError("Refusing to approve candidate without source_refs")
    if decision == "snooze":
        if not args.until:
            raise ValueError("--until is required for decision=snooze")
        try:
            datetime.strptime(args.until, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("--until must use YYYY-MM-DD") from exc
    if decision in {"approve", "snooze", "reject"} and not args.reviewed_by.strip():
        raise ValueError("--reviewed-by is required for this decision")

    status_by_decision = {
        "remind": "reminded",
        "approve": "approved",
        "snooze": "snoozed",
        "reject": "rejected",
    }
    updated: dict[str, object] = dict(candidate.meta)
    updated["updated"] = today()
    updated["status"] = status_by_decision[decision]
    updated["review_decision"] = decision
    updated["reviewed_at"] = today()
    updated["reviewed_by"] = args.reviewed_by or args.agent_id
    updated["review_reason"] = args.reason or ""
    updated["review_actor_role"] = role
    if decision == "remind":
        count = int(candidate.meta.get("reminder_count", "0") or "0") + 1
        updated["reminded_at"] = today()
        updated["reminder_count"] = count
    if decision == "snooze":
        updated["snoozed_until"] = args.until
    for key in ("tags", "source_refs", "contributor_agents", "source_sessions"):
        if key in updated:
            updated[key] = meta_list(candidate.meta, key)

    _, body = split_frontmatter(candidate.text)
    content = render_page(updated, body)
    if args.dry_run:
        if wants_json(args):
            emit_json({
                "ok": True,
                "dry_run": True,
                "candidate_path": candidate.rel,
                "status": updated["status"],
                "content": content,
            })
            return 0
        print(f"DRY RUN review {candidate.rel} -> {updated['status']}")
        return 0

    with RepoLock(timeout=args.lock_timeout), Transaction("review") as tx:
        tx.write_text(candidate.path, content)
        append_log(tx, "review", candidate.title, [
            f"candidate: {candidate.rel}",
            f"decision: {decision}",
            f"status: {updated['status']}",
            f"reviewed_by: {updated['reviewed_by']}",
            f"actor_role: {role}",
        ])
    if wants_json(args):
        emit_json({
            "ok": True,
            "candidate_path": candidate.rel,
            "status": updated["status"],
        })
        return 0
    print(f"Reviewed candidate: {candidate.rel} -> {updated['status']}")
    return 0


def command_respond(args: argparse.Namespace) -> int:
    role = require_role(args, "contributor", "respond")
    candidate = load_candidate(args.candidate)
    if candidate.status in TERMINAL_INBOX:
        raise ValueError(f"Candidate is already terminal: {candidate.status}")

    decision = args.decision
    if decision == "snooze":
        if not args.until:
            raise ValueError("--until is required for decision=snooze")
        try:
            datetime.strptime(args.until, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("--until must use YYYY-MM-DD") from exc
    if decision in {"capture", "snooze", "reject"} and not args.responded_by.strip():
        raise ValueError("--responded-by is required for this decision")

    status_by_decision = {
        "remind": "reminded",
        "capture": "reminded",
        "snooze": "snoozed",
        "reject": "rejected",
    }
    updated: dict[str, object] = dict(candidate.meta)
    updated["updated"] = today()
    updated["status"] = status_by_decision[decision]
    updated["user_decision"] = decision
    updated["responded_at"] = today()
    updated["responded_by"] = args.responded_by or args.agent_id
    updated["response_reason"] = args.reason or ""
    updated["response_actor_role"] = role
    if decision == "remind":
        count = int(candidate.meta.get("reminder_count", "0") or "0") + 1
        updated["reminded_at"] = today()
        updated["reminder_count"] = count
    if decision == "capture":
        updated["capture_requested_at"] = today()
        updated["capture_requested_by"] = args.responded_by
        updated["next_required_role"] = "reviewer-or-compiler"
    if decision == "snooze":
        updated["snoozed_until"] = args.until
    for key in ("tags", "source_refs", "contributor_agents", "source_sessions"):
        if key in updated:
            updated[key] = meta_list(candidate.meta, key)

    _, body = split_frontmatter(candidate.text)
    content = render_page(updated, body)
    if args.dry_run:
        if wants_json(args):
            emit_json({
                "ok": True,
                "dry_run": True,
                "candidate_path": candidate.rel,
                "status": updated["status"],
                "user_decision": decision,
                "content": content,
            })
            return 0
        print(f"DRY RUN respond {candidate.rel} -> {updated['status']}")
        return 0

    with RepoLock(timeout=args.lock_timeout), Transaction("respond") as tx:
        tx.write_text(candidate.path, content)
        append_log(tx, "respond", candidate.title, [
            f"candidate: {candidate.rel}",
            f"decision: {decision}",
            f"status: {updated['status']}",
            f"responded_by: {updated['responded_by']}",
            f"actor_role: {role}",
        ])
    if wants_json(args):
        emit_json({
            "ok": True,
            "candidate_path": candidate.rel,
            "status": updated["status"],
            "user_decision": decision,
        })
        return 0
    print(f"Recorded response: {candidate.rel} -> {updated['status']}")
    return 0


def command_promote(args: argparse.Namespace) -> int:
    role = require_role(args, "compiler", "promote")
    require_approval(args)
    candidate = load_candidate(args.candidate)
    if candidate.status in TERMINAL_INBOX:
        target = candidate.meta.get("graduated_to") or candidate.meta.get("merged_to")
        if wants_json(args):
            emit_json({
                "ok": True,
                "already_terminal": True,
                "status": candidate.status,
                "candidate": page_summary(candidate),
                "target": target,
            })
            return 0
        if target:
            print(f"Candidate already {candidate.status}: {target}")
            return 0
        print(f"Candidate already {candidate.status}.")
        return 0
    if candidate.status != "approved":
        raise ValueError(f"Candidate must be approved before promotion; current status={candidate.status}")
    if candidate.meta.get("sensitivity") == "secret":
        raise ValueError("Refusing to promote candidate with sensitivity=secret")
    source_refs = meta_list(candidate.meta, "source_refs")
    if not source_refs:
        raise ValueError("Refusing to promote candidate without source_refs")

    target_rel = normalize_target_path(args.target or candidate.meta.get("suggested_target", ""), candidate.meta)
    target_path = resolve_repo_path(target_rel)
    if target_path.exists():
        existing = find_page_by_rel(target_rel)
        if existing and existing.meta.get("origin_candidate") == candidate.rel:
            mark_candidate_terminal(candidate, target_rel, args, dry_run=args.dry_run)
            if wants_json(args):
                emit_json({
                    "ok": True,
                    "already_represented": True,
                    "candidate": page_summary(candidate),
                    "target": target_rel,
                })
                return 0
            print(f"Candidate already represented in wiki: {target_rel}")
            return 0
        raise FileExistsError(f"Target already exists: {target_rel}")

    _, candidate_body = split_frontmatter(candidate.text)
    wiki_meta: dict[str, object] = {
        "title": args.title or candidate.title,
        "created": candidate.meta.get("created", today()),
        "updated": today(),
        "type": candidate.meta.get("type", "concept"),
        "status": "active",
        "tags": [tag for tag in meta_list(candidate.meta, "tags") if tag != "implicit-capture"],
        "source_refs": source_refs,
        "origin_candidate": candidate.rel,
        "confidence": candidate.meta.get("confidence", "medium"),
    }
    wiki_body = candidate_body if candidate_body.strip() else f"# {candidate.title}\n"
    wiki_text = render_page(wiki_meta, wiki_body)

    updated_candidate_text = render_page(
        promoted_candidate_meta(candidate.meta, target_rel, args),
        candidate_body,
    )
    index_text = update_index(target_rel, str(wiki_meta["title"]), str(wiki_meta["type"]), args.summary or candidate.meta.get("value_reason", "已审核正式知识"))
    log_lines = [
        f"candidate: {candidate.rel}",
        f"target: {target_rel}",
        f"approved_by: {args.approved_by}",
        f"scope: {args.scope}",
        f"actor_role: {role}",
    ]

    if args.dry_run:
        if wants_json(args):
            emit_json({
                "ok": True,
                "dry_run": True,
                "candidate_path": candidate.rel,
                "target": target_rel,
                "wiki_meta": wiki_meta,
                "content": wiki_text,
            })
            return 0
        print(f"DRY RUN promote {candidate.rel} -> {target_rel}")
        print(wiki_text)
        return 0

    with RepoLock(timeout=args.lock_timeout), Transaction("promote") as tx:
        tx.write_text(target_path, wiki_text)
        tx.write_text(candidate.path, updated_candidate_text)
        tx.write_text(ROOT / "index.md", index_text)
        append_log(tx, "promote", str(wiki_meta["title"]), log_lines)
    if wants_json(args):
        emit_json({
            "ok": True,
            "promoted": True,
            "candidate_path": candidate.rel,
            "target": target_rel,
            "title": wiki_meta["title"],
        })
        return 0
    print(f"Promoted candidate: {candidate.rel} -> {target_rel}")
    return 0


def command_merge(args: argparse.Namespace) -> int:
    role = require_role(args, "compiler", "merge")
    require_approval(args)
    candidate = load_candidate(args.candidate)
    if candidate.status in TERMINAL_INBOX:
        raise ValueError(f"Candidate is already terminal: {candidate.status}")
    if candidate.status != "approved":
        raise ValueError(f"Candidate must be approved before merge; current status={candidate.status}")
    if candidate.meta.get("sensitivity") == "secret":
        raise ValueError("Refusing to merge candidate with sensitivity=secret")

    target_rel = normalize_target_path(args.target or candidate.meta.get("suggested_target", ""), candidate.meta)
    target = find_page_by_rel(target_rel)
    if not target or target.layer != "wiki":
        raise FileNotFoundError(f"Wiki target not found: {target_rel}")

    source_refs = unique([
        *meta_list(target.meta, "source_refs"),
        *meta_list(candidate.meta, "source_refs"),
    ])
    if not source_refs:
        raise ValueError("Refusing to merge candidate without source_refs")
    tags = unique([
        *meta_list(target.meta, "tags"),
        *[tag for tag in meta_list(candidate.meta, "tags") if tag != "implicit-capture"],
    ])

    target_meta: dict[str, object] = dict(target.meta)
    target_meta["updated"] = today()
    target_meta["source_refs"] = source_refs
    target_meta["tags"] = tags
    if target.meta.get("origin_candidate"):
        target_meta["origin_candidate"] = target.meta["origin_candidate"]

    _, target_body = split_frontmatter(target.text)
    _, candidate_body = split_frontmatter(candidate.text)
    addition = strip_leading_title(candidate_body).strip()
    merged_body = target_body.rstrip()
    if addition and normalize_for_fingerprint(addition) not in normalize_for_fingerprint(target_body):
        merged_body += f"\n\n## 增量更新 {today()}\n\n{addition}\n"

    candidate_meta: dict[str, object] = dict(candidate.meta)
    candidate_meta["updated"] = today()
    candidate_meta["status"] = "merged"
    candidate_meta["review_decision"] = "approved"
    candidate_meta["reviewed_by"] = args.approved_by
    candidate_meta["review_scope"] = args.scope
    candidate_meta["merged_to"] = target_rel
    for key in ("tags", "source_refs", "contributor_agents", "source_sessions"):
        if key in candidate_meta:
            candidate_meta[key] = meta_list(candidate.meta, key)

    target_text = render_page(target_meta, merged_body)
    candidate_text = render_page(candidate_meta, candidate_body)
    if args.dry_run:
        if wants_json(args):
            emit_json({
                "ok": True,
                "dry_run": True,
                "candidate_path": candidate.rel,
                "target": target_rel,
                "content": target_text,
            })
            return 0
        print(f"DRY RUN merge {candidate.rel} -> {target_rel}")
        return 0

    with RepoLock(timeout=args.lock_timeout), Transaction("merge") as tx:
        tx.write_text(target.path, target_text)
        tx.write_text(candidate.path, candidate_text)
        append_log(tx, "merge", candidate.title, [
            f"candidate: {candidate.rel}",
            f"target: {target_rel}",
            f"approved_by: {args.approved_by}",
            f"scope: {args.scope}",
            f"actor_role: {role}",
        ])
    if wants_json(args):
        emit_json({
            "ok": True,
            "merged": True,
            "candidate_path": candidate.rel,
            "target": target_rel,
        })
        return 0
    print(f"Merged candidate: {candidate.rel} -> {target_rel}")
    return 0


def command_dashboard(args: argparse.Namespace) -> int:
    require_role(args, "reviewer", "dashboard")
    pages = iter_markdown()
    output_rel = args.output.replace("\\", "/")
    output_path = resolve_docs_output(output_rel)
    text = render_dashboard(pages)
    if args.dry_run:
        if wants_json(args):
            emit_json({"ok": True, "dry_run": True, "output": output_rel, "content": text})
            return 0
        print(text)
        return 0

    with RepoLock(timeout=args.lock_timeout), Transaction("dashboard") as tx:
        tx.write_text(output_path, text)
        append_log(tx, "dashboard", "Obsidian 审核面板", [
            f"output: {output_rel}",
            "source: km dashboard",
        ])
    if wants_json(args):
        emit_json({"ok": True, "output": output_rel})
        return 0
    print(f"Updated dashboard: {output_rel}")
    return 0


def command_qmd_readiness(args: argparse.Namespace) -> int:
    require_role(args, "reviewer", "qmd-readiness")
    pages = iter_markdown()
    wiki = [page for page in pages if page.layer == "wiki"]
    raw = [page for page in pages if page.layer == "raw"]
    index = {
        "wiki_pages": len(wiki),
        "raw_sources": len(raw),
        "qmd_available": shutil.which("qmd") is not None,
        "thresholds": {
            "wiki_pages": 500,
            "raw_sources": 1000,
            "top5_hit_rate": 0.90,
        },
    }
    query_results = [qmd_query_result(query) for query in QMD_READINESS_QUERIES]
    top5_hit_rate = sum(1 for item in query_results if item["hit"]) / max(len(query_results), 1)
    ready = (
        index["qmd_available"]
        and index["wiki_pages"] >= index["thresholds"]["wiki_pages"]
        and index["raw_sources"] >= index["thresholds"]["raw_sources"]
        and top5_hit_rate >= index["thresholds"]["top5_hit_rate"]
    )
    report = {
        "ok": True,
        "ready": ready,
        "index": index,
        "top5_hit_rate": top5_hit_rate,
        "queries": query_results,
        "recommendation": "enable qmd" if ready else "defer qmd and continue using base search",
    }
    text = render_qmd_readiness(report)
    if args.output:
        output_path = resolve_docs_output(args.output)
        if args.dry_run:
            if wants_json(args):
                emit_json({"ok": True, "dry_run": True, "output": args.output, "content": text, **report})
                return 0
            print(text)
            return 0
        with RepoLock(timeout=args.lock_timeout), Transaction("qmd-readiness") as tx:
            tx.write_text(output_path, text)
            append_log(tx, "qmd-readiness", "QMD 就绪报告", [
                f"output: {args.output}",
                f"ready: {ready}",
            ])
        report["output"] = args.output
    if wants_json(args):
        emit_json(report)
        return 0
    print(text)
    return 0


def render_dashboard(pages: list[Page]) -> str:
    wiki = [page for page in pages if page.layer == "wiki"]
    inbox = [page for page in pages if page.layer == "inbox"]
    raw = [page for page in pages if page.layer == "raw"]
    active_inbox = [page for page in inbox if page.status not in TERMINAL_INBOX]
    graduated = [page for page in inbox if page.status in {"graduated", "merged"}]
    rejected = [page for page in inbox if page.status == "rejected"]

    lines = [
        "# AgentsKM 审核面板",
        "",
        "> 由 `python tools/km-cli/km.py dashboard` 生成。用于 Obsidian 中快速审核 Inbox、查看正式 Wiki 和 Raw 来源。",
        "",
        f"更新时间：{datetime.now().isoformat(timespec='seconds')}",
        "",
        "## 总览",
        "",
        "| 层级 | 数量 |",
        "|---|---:|",
        f"| Wiki 正式页 | {len(wiki)} |",
        f"| Inbox 待处理 | {len(active_inbox)} |",
        f"| Inbox 已毕业/已合并 | {len(graduated)} |",
        f"| Inbox 已拒绝 | {len(rejected)} |",
        f"| Raw 来源 | {len(raw)} |",
        "",
        "## 待处理 Inbox",
        "",
    ]
    lines.extend(render_page_table(active_inbox, include_target=True) if active_inbox else ["暂无待处理候选。"])
    lines.extend([
        "",
        "## 已毕业或已合并 Inbox",
        "",
    ])
    lines.extend(render_page_table(graduated, include_target=True) if graduated else ["暂无已毕业记录。"])
    lines.extend([
        "",
        "## 正式 Wiki",
        "",
    ])
    lines.extend(render_page_table(wiki, include_target=False) if wiki else ["暂无正式 Wiki 页。"])
    lines.extend([
        "",
        "## Raw 来源",
        "",
    ])
    lines.extend(render_page_table(raw, include_target=False) if raw else ["暂无 Raw 来源。"])
    lines.extend([
        "",
        "## 操作入口",
        "",
        "```powershell",
        "python tools\\km-cli\\km.py pending",
        "python tools\\km-cli\\km.py search \"领星 API 鉴权\"",
        "python tools\\km-cli\\km.py validate",
        "python tools\\km-cli\\km.py lint",
        "```",
        "",
    ])
    return "\n".join(lines)


def qmd_query_result(query: str) -> dict[str, object]:
    payload, _ = search_pages(query, limit=5)
    hit = bool(payload["matches"]) and payload["matches"][0]["layer"] == "wiki"
    return {
        "query": query,
        "hit": hit,
        "top_result": payload["matches"][0]["path"] if payload["matches"] else "",
        "layer": payload["matches"][0]["layer"] if payload["matches"] else "",
    }


def render_qmd_readiness(report: dict[str, object]) -> str:
    index = report["index"]
    lines = [
        "# QMD Readiness",
        "",
        f"- QMD available: {index['qmd_available']}",
        f"- Wiki pages: {index['wiki_pages']} / {index['thresholds']['wiki_pages']}",
        f"- Raw sources: {index['raw_sources']} / {index['thresholds']['raw_sources']}",
        f"- Top-5 hit rate: {report['top5_hit_rate']:.0%} / {index['thresholds']['top5_hit_rate']:.0%}",
        f"- Recommendation: {report['recommendation']}",
        "",
        "## Fixed Queries",
        "",
        "| Query | Hit | Top Result | Layer |",
        "|---|---|---|---|",
    ]
    for item in report["queries"]:
        lines.append(
            f"| {escape_table(item['query'])} | {item['hit']} | {escape_table(item['top_result'] or '-')} | {escape_table(item['layer'] or '-')} |"
        )
    lines.append("")
    return "\n".join(lines)


def search_pages(query: str, limit: int = 10) -> tuple[dict[str, object], list[tuple[int, Page, str]]]:
    normalized = query.casefold()
    tokens = tokenize_query(query)
    layer_rank = {"wiki": 0, "inbox": 1, "raw": 2}
    matches: list[tuple[int, int, Page, str]] = []
    for page in iter_markdown():
        if page.layer not in layer_rank:
            continue
        score, idx = score_page(page, normalized, tokens)
        if score <= 0 or idx < 0:
            continue
        snippet = compact_snippet(page.text, idx, len(query))
        matches.append((score, layer_rank[page.layer], page, snippet))
    limited = sorted(matches, key=lambda item: (item[1], -item[0], item[2].rel))[:limit]
    payload = {
        "ok": True,
        "query": query,
        "count": len(limited),
        "matches": [dict(page_summary(page, snippet), score=score) for score, _, page, snippet in limited],
    }
    raw_matches = [(rank, page, snippet) for score, rank, page, snippet in limited]
    return payload, raw_matches


def tokenize_query(query: str) -> list[str]:
    tokens: list[str] = []
    for chunk in re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]+", query.casefold()):
        if chunk in QUERY_STOPWORDS:
            continue
        tokens.append(chunk)
        for prefix in ("怎么", "如何", "怎样", "请问", "请"):
            if chunk.startswith(prefix) and len(chunk) > len(prefix):
                remainder = chunk[len(prefix):]
                if remainder and remainder not in QUERY_STOPWORDS:
                    tokens.append(remainder)
    return unique(tokens)


def score_page(page: Page, normalized_query: str, tokens: list[str]) -> tuple[int, int]:
    title = page.title.casefold()
    rel = page.rel.casefold()
    tags = " ".join(meta_list(page.meta, "tags")).casefold()
    refs = " ".join(meta_list(page.meta, "source_refs")).casefold()
    body = page.text.casefold()
    blob = "\n".join([title, rel, tags, refs, body[:5000]])
    score = 0
    best_idx = -1

    if normalized_query in title:
        score += 50
        best_idx = body.find(normalized_query)
    elif normalized_query in body:
        score += 25
        best_idx = body.find(normalized_query)

    if tokens:
        token_hits = 0
        for token in tokens:
            token_idx = blob.find(token)
            if token_idx >= 0:
                token_hits += 1
                if best_idx < 0:
                    best_idx = body.find(token)
                if token in title:
                    score += 15
                elif token in rel or token in tags:
                    score += 10
                elif token in refs:
                    score += 6
                else:
                    score += 4
        if token_hits == len(tokens):
            score += 20
    if best_idx < 0:
        for token in tokens or [normalized_query]:
            idx = body.find(token)
            if idx >= 0:
                best_idx = idx
                break
    return score, best_idx


def render_page_table(pages: list[Page], include_target: bool) -> list[str]:
    header = "| 状态 | 类型 | 页面 | 标签 | 来源/目标 |" if include_target else "| 状态 | 类型 | 页面 | 标签 | 来源 |"
    lines = [header, "|---|---|---|---|---|"]
    for page in sorted(pages, key=lambda item: (item.status, item.rel)):
        status = page.status or "-"
        page_type = page.meta.get("type", "-")
        link = f"[{escape_table(page.title)}](../{page.rel})" if page.rel.startswith(("wiki/", "raw/", "000_Inbox/")) else f"[{escape_table(page.title)}]({page.rel})"
        tags = ", ".join(meta_list(page.meta, "tags")) or "-"
        refs = ", ".join(meta_list(page.meta, "source_refs"))
        target = page.meta.get("suggested_target") or page.meta.get("graduated_to") or page.meta.get("merged_to")
        last = target or refs or "-"
        lines.append(f"| {escape_table(status)} | {escape_table(page_type)} | {link} | {escape_table(tags)} | {escape_table(last)} |")
    return lines


def escape_table(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def load_candidate(value: str) -> Page:
    rel = value.replace("\\", "/").strip()
    if not rel.startswith("000_Inbox/"):
        rel = f"000_Inbox/{rel}"
    if not rel.endswith(".md"):
        rel = f"{rel}.md"
    page = find_page_by_rel(rel)
    if not page:
        raise FileNotFoundError(f"Candidate not found: {rel}")
    if page.layer != "inbox":
        raise ValueError(f"Not an inbox candidate: {rel}")
    return page


def normalize_target_path(value: str, meta: dict[str, str]) -> str:
    if not value:
        page_type = meta.get("type", "concept")
        folder = WIKI_DIRS.get(page_type, "wiki/concepts")
        slug = slugify(meta.get("title", "")) or Path(meta.get("id", "candidate")).stem
        value = f"{folder}/{slug}.md"
    value = value.replace("\\", "/").strip("/")
    if not value.endswith(".md"):
        value = f"{value}.md"
    resolved = resolve_repo_path(value)
    allowed_roots = [(ROOT / prefix).resolve() for prefix in set(WIKI_DIRS.values())]
    if not any(root in resolved.parents for root in allowed_roots):
        raise ValueError(f"Target must be inside wiki categories: {value}")
    return resolved.relative_to(ROOT.resolve()).as_posix()


def resolve_docs_output(value: str) -> Path:
    resolved = resolve_repo_path(value)
    docs_root = (ROOT / "docs").resolve()
    if docs_root not in resolved.parents or resolved.suffix.casefold() != ".md":
        raise ValueError(f"Generated reports must be Markdown files inside docs/: {value}")
    return resolved


def promoted_candidate_meta(meta: dict[str, str], target_rel: str, args: argparse.Namespace) -> dict[str, object]:
    updated: dict[str, object] = dict(meta)
    updated["updated"] = today()
    updated["status"] = "graduated"
    updated["reviewed_at"] = today()
    updated["review_decision"] = "approved"
    updated["reviewed_by"] = args.approved_by
    updated["review_scope"] = args.scope
    updated["graduated_to"] = target_rel
    for key in ("tags", "source_refs"):
        if key in updated:
            updated[key] = meta_list(meta, key)
    return updated


def mark_candidate_terminal(candidate: Page, target_rel: str, args: argparse.Namespace, dry_run: bool) -> None:
    if dry_run:
        return
    _, body = split_frontmatter(candidate.text)
    with RepoLock(timeout=args.lock_timeout), Transaction("mark-candidate") as tx:
        tx.write_text(candidate.path, render_page(promoted_candidate_meta(candidate.meta, target_rel, args), body))
        append_log(tx, "promote-idempotent", candidate.title, [
            f"candidate: {candidate.rel}",
            f"target: {target_rel}",
        ])


def update_index(target_rel: str, title: str, page_type: str, summary: str) -> str:
    index_path = ROOT / "index.md"
    text = index_path.read_text(encoding="utf-8")
    if f"]({target_rel})" in text:
        return text
    section = WIKI_SECTION.get(page_type, "Concepts")
    line = f"- [{title}]({target_rel}) — {summary}"
    pattern = re.compile(rf"(## {re.escape(section)}\n)(.*?)(?=\n## |\Z)", re.DOTALL)
    match = pattern.search(text)
    if not match:
        return text.rstrip() + f"\n\n## {section}\n\n{line}\n"
    body = match.group(2).strip("\n")
    new_body = f"\n{line}\n" if not body else f"\n{body}\n{line}\n"
    return text[:match.start(2)] + new_body + text[match.end(2):]


def append_log(tx: Transaction, action: str, subject: str, lines: list[str]) -> None:
    log_path = ROOT / "log.md"
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else "# Wiki Log\n"
    entry = [f"## [{today()}] {action} | {subject}"]
    entry.extend(f"- {line}" for line in lines)
    tx.write_text(log_path, existing.rstrip() + "\n\n" + "\n".join(entry) + "\n")


def load_body(body: str | None, body_file: str | None, title: str, value_reason: str) -> str:
    if body_file:
        path = resolve_repo_path(body_file)
        return path.read_text(encoding="utf-8")
    if body:
        return body if body.startswith("# ") else f"# {title}\n\n{body}\n"
    return f"# {title}\n\n## 价值\n\n{value_reason}\n"


def strip_leading_title(body: str) -> str:
    return re.sub(r"^# [^\n]+\n+", "", body.lstrip(), count=1)


def parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def find_duplicate_fingerprint(value: str) -> Page | None:
    for page in iter_markdown():
        if page.layer == "inbox" and page.meta.get("fingerprint") == value:
            return page
    return None


def find_duplicate_candidate(value: str, title: str, suggested_target: str) -> Page | None:
    exact = find_duplicate_fingerprint(value)
    if exact:
        return exact
    normalized_title = normalize_for_fingerprint(title)
    normalized_target = suggested_target.replace("\\", "/").strip().casefold()
    for page in iter_markdown():
        if page.layer != "inbox" or page.status in TERMINAL_INBOX:
            continue
        same_title = normalize_for_fingerprint(page.title) == normalized_title
        page_target = page.meta.get("suggested_target", "").replace("\\", "/").strip().casefold()
        same_target = bool(normalized_target) and page_target == normalized_target
        if same_title or same_target:
            return page
    return None


def update_duplicate_candidate(
    candidate: Page,
    args: argparse.Namespace,
    source_refs: list[str],
    dry_run: bool,
) -> bool:
    updated: dict[str, object] = dict(candidate.meta)
    merged_refs = unique([*meta_list(candidate.meta, "source_refs"), *source_refs])
    merged_agents = unique([
        *meta_list(candidate.meta, "contributor_agents"),
        candidate.meta.get("agent_id", ""),
        args.agent_id,
    ])
    merged_sessions = unique([
        *meta_list(candidate.meta, "source_sessions"),
        candidate.meta.get("source_session", ""),
        args.source_session,
    ])
    changed = (
        merged_refs != meta_list(candidate.meta, "source_refs")
        or merged_agents != meta_list(candidate.meta, "contributor_agents")
        or merged_sessions != meta_list(candidate.meta, "source_sessions")
    )
    if not changed or dry_run:
        return changed
    updated["updated"] = today()
    updated["source_refs"] = merged_refs
    updated["contributor_agents"] = [item for item in merged_agents if item]
    updated["source_sessions"] = [item for item in merged_sessions if item]
    if candidate.status == "pending-source-review" and merged_refs:
        updated["status"] = "pending"
    if "tags" in updated:
        updated["tags"] = meta_list(candidate.meta, "tags")
    _, body = split_frontmatter(candidate.text)
    with RepoLock(timeout=args.lock_timeout), Transaction("propose-duplicate") as tx:
        tx.write_text(candidate.path, render_page(updated, body))
        append_log(tx, "propose-duplicate", candidate.title, [
            f"candidate: {candidate.rel}",
            f"agent_id: {args.agent_id}",
            f"source_session: {args.source_session}",
        ])
    return True


def setup_command_hint(profile: str) -> str:
    return f'"{sys.executable}" "{Path(__file__).resolve()}" setup --profile {profile}'


def recommended_vault_path() -> Path:
    if CONFIG_PATH == get_config_path():
        return DEFAULT_VAULT.resolve()
    return (CONFIG_PATH.parent / "vault").resolve()


def command_doctor(args: argparse.Namespace) -> int:
    status = inspect_setup(CONFIG_PATH, args.profile)
    checks: list[dict[str, object]] = [
        {
            "name": "config",
            "ok": status.get("state") not in {"config_invalid", "legacy_config"},
            "detail": str(status.get("message", "")),
        }
    ]
    vault_path_text = status.get("vault_path")
    if vault_path_text:
        vault_path = Path(str(vault_path_text))
        checks.extend([
            {"name": "vault_exists", "ok": vault_path.is_dir(), "detail": str(vault_path)},
            {"name": "vault_layout", "ok": vault_is_valid(vault_path), "detail": str(vault_path)},
            {"name": "vault_writable", "ok": os.access(vault_path, os.W_OK), "detail": str(vault_path)},
            {
                "name": "stale_locks",
                "ok": not (vault_path / ".km" / "locks").exists()
                or not any((vault_path / ".km" / "locks").glob("*.lock")),
                "detail": str(vault_path / ".km" / "locks"),
            },
        ])
    ready = bool(status.get("configured")) and all(bool(item["ok"]) for item in checks)
    payload = {
        "ok": ready,
        "toolkit_version": TOOLKIT_VERSION,
        "repository": TOOLKIT_REPOSITORY,
        "config_path": str(CONFIG_PATH),
        "configuration_source": "config_file",
        "environment_configuration": "ignored",
        "profile": status.get("profile", status.get("requested_profile")),
        "role": status.get("role"),
        "vault_path": vault_path_text,
        "state": status.get("state"),
        "checks": checks,
        "next_action": "ready" if ready else status.get("next_action", setup_command_hint(str(status.get("requested_profile", "default")))),
    }
    if wants_json(args):
        emit_json(payload)
        return 0 if ready else 1
    print(f"AgentsKM doctor: {'ready' if ready else 'attention required'}")
    print(f"Version: {TOOLKIT_VERSION}")
    print(f"Config: {CONFIG_PATH}")
    for check in checks:
        print(f"[{'ok' if check['ok'] else 'fail'}] {check['name']}: {check['detail']}")
    print(f"Next: {payload['next_action']}")
    return 0 if ready else 1


def run_update_process(command: list[str], cwd: Path) -> dict[str, object]:
    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            encoding="utf-8",
            capture_output=True,
        )
    except OSError as exc:
        raise RuntimeError(f"Cannot start update command ({' '.join(command)}): {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "update command failed").strip()
        raise RuntimeError(f"Update command failed ({' '.join(command)}): {detail}")
    return {
        "command": command,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def command_launcher(name: str) -> list[str]:
    if os.name == "nt":
        cmd_path = shutil.which(f"{name}.cmd")
        if cmd_path:
            return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", cmd_path]
        exe_path = shutil.which(f"{name}.exe")
        if exe_path:
            return [exe_path]
    path = shutil.which(name)
    if path:
        return [path]
    raise RuntimeError(f"Required update command was not found on PATH: {name}")


def is_packaged_runtime() -> bool:
    return (TOOL_ROOT / "__init__.py").exists() and (TOOL_ROOT / "cli.py").exists()


def emit_update_payload(args: argparse.Namespace, payload: dict[str, object]) -> int:
    if wants_json(args):
        emit_json(payload)
        return 0
    print(f"AgentsKM update: {payload['mode']}")
    print("Update completed." if not args.check else "Update check completed.")
    if payload.get("restart_required"):
        print("Start a new conversation or reconnect the AgentsKM MCP server to load the new code.")
    return 0


def command_packaged_update(args: argparse.Namespace) -> int:
    restart_required = not args.check
    return emit_update_payload(args, {
        "ok": True,
        "mode": "packaged_runtime",
        "repository": TOOLKIT_REPOSITORY,
        "current_process_version": TOOLKIT_VERSION,
        "check_only": bool(args.check),
        "supports_in_process_update": False,
        "updated": False,
        "steps": [],
        "restart_required": restart_required,
        "recommended_mcp_command": [
            "uvx",
            "--from",
            "agentskm-toolkit",
            "agentskm",
            "mcp",
        ],
        "next_action": (
            "reconnect_mcp_to_let_the_host_resolve_the_latest_package"
            if restart_required else
            "compare_current_process_version_with_the_package_index_or_git_release"
        ),
    })


def command_update(args: argparse.Namespace) -> int:
    steps: list[dict[str, object]] = []
    if (TOOL_ROOT / ".git").is_dir():
        dirty = run_update_process(["git", "status", "--porcelain"], TOOL_ROOT)["stdout"]
        if dirty:
            raise RuntimeError("Toolkit checkout has local changes; commit or stash them before update")
        steps.append(run_update_process(["git", "fetch", "origin", "main"], TOOL_ROOT))
        if not args.check:
            steps.append(run_update_process(["git", "merge", "--ff-only", "origin/main"], TOOL_ROOT))
            build_script = TOOL_ROOT / "scripts" / "build_plugin.py"
            if build_script.exists():
                steps.append(run_update_process([sys.executable, str(build_script)], TOOL_ROOT))
        mode = "git_checkout"
        restart_required = not args.check
    else:
        if is_packaged_runtime():
            return command_packaged_update(args)
        host = args.host or "codex"
        if host != "codex":
            raise RuntimeError(
                "This packaged host has no supported self-update driver. Reinstall the plugin package from "
                f"{TOOLKIT_REPOSITORY}."
            )
        codex = command_launcher("codex")
        listed = run_update_process(
            [*codex, "plugin", "marketplace", "list", "--json"], TOOL_ROOT
        )
        steps.append(listed)
        try:
            marketplace_data = json.loads(str(listed["stdout"]))
            marketplace_item = next(
                item for item in marketplace_data.get("marketplaces", [])
                if item.get("name") == args.marketplace
            )
            marketplace_root = Path(str(marketplace_item["root"])).resolve()
        except (json.JSONDecodeError, KeyError, StopIteration, TypeError) as exc:
            raise RuntimeError(f"Codex marketplace is not configured: {args.marketplace}") from exc

        local_checkout = (marketplace_root / ".git").is_dir()
        if local_checkout:
            dirty = run_update_process(
                ["git", "status", "--porcelain"], marketplace_root
            )["stdout"]
            steps.append({
                "command": ["git", "status", "--porcelain"],
                "stdout": str(dirty),
                "stderr": "",
                "dirty": bool(dirty),
            })
            if dirty and not args.check:
                raise RuntimeError(
                    f"Local marketplace checkout has changes: {marketplace_root}; "
                    "commit or stash them before update"
                )
            if not dirty:
                steps.append(run_update_process(
                    ["git", "fetch", "origin", "main"], marketplace_root
                ))
                if not args.check:
                    steps.append(run_update_process(
                        ["git", "merge", "--ff-only", "origin/main"], marketplace_root
                    ))
                    build_script = marketplace_root / "scripts" / "build_plugin.py"
                    if build_script.exists():
                        steps.append(run_update_process(
                            [sys.executable, str(build_script)], marketplace_root
                        ))
            mode = "codex_local_git_marketplace"
        else:
            steps.append(run_update_process(
                [*codex, "plugin", "marketplace", "upgrade", args.marketplace, "--json"],
                TOOL_ROOT,
            ))
            mode = "codex_git_marketplace"
        if not args.check:
            steps.append(run_update_process(
                [*codex, "plugin", "add", f"{CODEX_PLUGIN}@{args.marketplace}", "--json"],
                TOOL_ROOT,
            ))
        restart_required = not args.check
    payload = {
        "ok": True,
        "mode": mode,
        "repository": TOOLKIT_REPOSITORY,
        "current_process_version": TOOLKIT_VERSION,
        "check_only": bool(args.check),
        "steps": steps,
        "restart_required": restart_required,
        "next_action": (
            "start_new_conversation_or_reconnect_mcp" if restart_required else "none"
        ),
    }
    return emit_update_payload(args, payload)


def command_setup_status(args: argparse.Namespace) -> int:
    payload = inspect_setup(CONFIG_PATH, args.profile)
    payload["setup_command"] = setup_command_hint(str(payload["requested_profile"]))
    payload["recommended_vault_path"] = str(recommended_vault_path())
    payload["next_action"] = (
        "ready" if payload["configured"] else "run_setup_or_start_the_plugin_once"
    )
    payload["restart_required_after_setup"] = False
    if wants_json(args):
        emit_json(payload)
        return 0
    print(f"AgentsKM setup: {payload['state']}")
    print(payload["message"])
    print(f"Config: {CONFIG_PATH}")
    if not payload["configured"]:
        print(f"Setup: {payload['setup_command']}")
    return 0


def prepare_setup_config(args: argparse.Namespace) -> tuple[dict[str, object], bool, bool, bool]:
    migrated = False
    vault_initialized = False
    config_created = not CONFIG_PATH.exists()
    if CONFIG_PATH.exists():
        config = read_json(CONFIG_PATH)
        if is_legacy_config(config):
            legacy_vault = Path(str(config["vault"])).expanduser().resolve()
            config = default_config(args.vault_name, legacy_vault)
            migrated = True
        else:
            errors = validate_config(config)
            if errors:
                raise ValueError("Invalid AgentsKM config: " + "; ".join(errors))
    else:
        initial_vault = Path(args.vault).expanduser().resolve() if args.vault else recommended_vault_path()
        config = default_config(
            args.vault_name,
            initial_vault,
            profile_name=args.profile,
            display_name=args.display_name,
            host=args.host,
            actor_id=args.actor_id,
            role=args.role,
        )

    vaults = config["vaults"]
    if args.vault_name in vaults:
        configured_vault = Path(vaults[args.vault_name]["path"]).expanduser().resolve()
        if args.vault and configured_vault != Path(args.vault).expanduser().resolve():
            raise ValueError(
                f"Vault name already points elsewhere: {args.vault_name} -> {configured_vault}"
            )
        vault_path = configured_vault
    else:
        if not args.vault:
            raise ValueError(f"--vault is required for new vault name: {args.vault_name}")
        vault_path = Path(args.vault).expanduser().resolve()
        vaults[args.vault_name] = {
            "path": str(vault_path),
            "create_if_missing": False,
        }
    if not vault_is_valid(vault_path):
        if args.dry_run:
            vault_initialized = True
        else:
            vault_initialized = initialize_empty_vault(vault_path)

    expected = {
        "display_name": args.display_name or args.profile,
        "host": args.host,
        "actor_id": args.actor_id or args.profile,
        "role": args.role,
        "vault": args.vault_name,
        "enabled": True,
    }
    profiles = config["profiles"]
    changed = migrated or config_created
    existing_profile = profiles.get(args.profile)
    existing_compiler = (
        isinstance(existing_profile, dict)
        and existing_profile.get("role") == "compiler"
        and existing_profile.get("host") == expected["host"]
        and existing_profile.get("actor_id") == expected["actor_id"]
        and existing_profile.get("vault") == expected["vault"]
    )
    if args.role == "compiler" and not args.confirm_compiler and not existing_compiler:
        raise ValueError("Creating a compiler profile requires --confirm-compiler")
    if args.profile in profiles:
        current = profiles[args.profile]
        core_fields = ("host", "actor_id", "role", "vault", "enabled")
        conflicts = [key for key in core_fields if current.get(key, True) != expected[key]]
        if conflicts:
            details = ", ".join(
                f"{key}: {current.get(key)!r} -> {expected[key]!r}" for key in conflicts
            )
            raise ValueError(
                f"Profile already exists with different settings: {args.profile}; {details}"
            )
    else:
        profiles[args.profile] = expected
        changed = True

    errors = validate_config(config)
    if errors:
        raise ValueError("Generated AgentsKM config is invalid: " + "; ".join(errors))
    return config, changed, migrated, vault_initialized


def command_setup(args: argparse.Namespace) -> int:
    with ConfigLock(timeout=args.lock_timeout):
        config, changed, migrated, vault_initialized = prepare_setup_config(args)
        content = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
        if changed and not args.dry_run:
            if migrated:
                backup = CONFIG_PATH.with_suffix(CONFIG_PATH.suffix + ".v0.bak")
                if not backup.exists():
                    shutil.copy2(CONFIG_PATH, backup)
            atomic_write(CONFIG_PATH, content)

    state = "configured" if changed else "already_configured"
    payload = {
        "ok": True,
        "configured": True,
        "state": state,
        "changed": changed,
        "dry_run": bool(args.dry_run),
        "migrated_legacy_config": migrated,
        "vault_initialized": vault_initialized,
        "config_path": str(CONFIG_PATH),
        "profile": args.profile,
        "role": args.role,
        "vault_name": args.vault_name,
        "vault_path": config["vaults"][args.vault_name]["path"],
        "restart_required": False,
        "next_action": "ready",
    }
    if args.dry_run:
        payload["preview"] = config
    if wants_json(args):
        emit_json(payload)
        return 0
    print(f"AgentsKM setup: {state}")
    print(f"Profile: {args.profile} ({args.role})")
    print(f"Vault: {payload['vault_path']}")
    if vault_initialized:
        print("Initialized an empty AgentsKM Vault with local usage instructions.")
    return 0


def command_configure(args: argparse.Namespace) -> int:
    print("WARNING: `configure` is deprecated; use `setup` with an Agent Profile.", file=sys.stderr)
    setup_args = argparse.Namespace(
        profile="default",
        display_name="Unknown local agent",
        host="unknown",
        actor_id="local-default",
        role="contributor",
        vault_name="main",
        vault=args.vault,
        confirm_compiler=False,
        dry_run=args.dry_run,
        lock_timeout=args.lock_timeout,
        json=args.json,
    )
    return command_setup(setup_args)


def add_common_write_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--lock-timeout", type=float, default=10.0)


def add_json_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")


def add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="Override the user config file path (diagnostics and tests)")


def add_runtime_args(parser: argparse.ArgumentParser) -> None:
    add_config_arg(parser)
    parser.add_argument("--profile", help="Select a configured Agent Profile")


def main(argv: list[str] | None = None) -> int:
    global CONFIG_PATH
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(prog="km")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_status = subparsers.add_parser("setup-status", help="Check AgentsKM configuration and Profile readiness")
    setup_status.add_argument("--profile")
    add_config_arg(setup_status)
    add_json_arg(setup_status)
    setup_status.set_defaults(func=command_setup_status)

    setup = subparsers.add_parser("setup", help="Create or extend the AgentsKM user configuration")
    setup.add_argument("--profile", required=True)
    setup.add_argument("--display-name")
    setup.add_argument("--host", default="generic")
    setup.add_argument("--actor-id")
    setup.add_argument("--role", choices=sorted(ROLE_ORDER), default="contributor")
    setup.add_argument("--vault-name", default="main")
    setup.add_argument("--vault")
    setup.add_argument("--confirm-compiler", action="store_true")
    add_config_arg(setup)
    add_json_arg(setup)
    setup.add_argument("--dry-run", action="store_true")
    setup.add_argument("--lock-timeout", type=float, default=10.0)
    setup.set_defaults(func=command_setup)

    configure = subparsers.add_parser("configure", help="Deprecated alias for contributor setup")
    configure.add_argument("--vault", required=True)
    add_config_arg(configure)
    add_json_arg(configure)
    add_common_write_args(configure)
    configure.set_defaults(func=command_configure)

    status = subparsers.add_parser("status", help="Show repository counts")
    add_runtime_args(status)
    add_json_arg(status)
    status.set_defaults(func=command_status)

    pending = subparsers.add_parser("pending", help="List active inbox candidates")
    add_runtime_args(pending)
    add_json_arg(pending)
    pending.set_defaults(func=command_pending)

    reminders = subparsers.add_parser("reminders", help="List new or due knowledge reminders")
    add_runtime_args(reminders)
    add_json_arg(reminders)
    reminders.set_defaults(func=command_reminders)

    search = subparsers.add_parser("search", help="Search wiki, inbox, raw, and docs")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)
    add_runtime_args(search)
    add_json_arg(search)
    search.set_defaults(func=command_search)

    validate = subparsers.add_parser("validate", help="Validate required frontmatter")
    add_runtime_args(validate)
    add_json_arg(validate)
    validate.set_defaults(func=command_validate)

    lint = subparsers.add_parser("lint", help="Check internal wiki links and misplaced pages")
    add_runtime_args(lint)
    add_json_arg(lint)
    lint.set_defaults(func=command_lint)

    propose = subparsers.add_parser("propose", help="Create an inbox candidate")
    propose.add_argument("--title", required=True)
    propose.add_argument("--type", default="note", choices=sorted(set(WIKI_DIRS.keys())))
    propose.add_argument("--tags", default="")
    propose.add_argument("--agent-id", default="codex")
    propose.add_argument("--source-tool", default="km-cli")
    propose.add_argument("--source-session", default="manual")
    propose.add_argument("--source-ref", action="append")
    propose.add_argument("--suggested-action", default="create", choices=["create", "merge", "hold", "reject"])
    propose.add_argument("--suggested-target", default="")
    propose.add_argument("--value-reason", required=True)
    propose.add_argument("--confidence", default="medium", choices=["high", "medium", "low"])
    propose.add_argument("--sensitivity", default="normal", choices=["normal", "sensitive"])
    propose.add_argument("--body")
    propose.add_argument("--body-file")
    propose.add_argument("--slug")
    add_runtime_args(propose)
    add_json_arg(propose)
    add_common_write_args(propose)
    propose.set_defaults(func=command_propose)

    review = subparsers.add_parser("review", help="Record a reminder or user review decision")
    review.add_argument("candidate")
    review.add_argument("--decision", required=True, choices=["remind", "approve", "snooze", "reject"])
    review.add_argument("--reviewed-by", default="")
    review.add_argument("--agent-id", default="agent")
    review.add_argument("--reason", default="")
    review.add_argument("--until")
    add_runtime_args(review)
    add_json_arg(review)
    add_common_write_args(review)
    review.set_defaults(func=command_review)

    respond = subparsers.add_parser("respond", help="Record contributor-visible user response without approving")
    respond.add_argument("candidate")
    respond.add_argument("--decision", required=True, choices=["remind", "capture", "snooze", "reject"])
    respond.add_argument("--responded-by", default="")
    respond.add_argument("--agent-id", default="agent")
    respond.add_argument("--reason", default="")
    respond.add_argument("--until")
    add_runtime_args(respond)
    add_json_arg(respond)
    add_common_write_args(respond)
    respond.set_defaults(func=command_respond)
    promote = subparsers.add_parser("promote", help="Promote an inbox candidate to wiki")
    promote.add_argument("candidate")
    promote.add_argument("--target")
    promote.add_argument("--title")
    promote.add_argument("--summary")
    promote.add_argument("--approved-by", required=True)
    promote.add_argument("--scope", required=True)
    add_runtime_args(promote)
    add_json_arg(promote)
    add_common_write_args(promote)
    promote.set_defaults(func=command_promote)

    merge = subparsers.add_parser("merge", help="Merge an approved candidate into an existing wiki page")
    merge.add_argument("candidate")
    merge.add_argument("--target", required=True)
    merge.add_argument("--approved-by", required=True)
    merge.add_argument("--scope", required=True)
    add_runtime_args(merge)
    add_json_arg(merge)
    add_common_write_args(merge)
    merge.set_defaults(func=command_merge)

    dashboard = subparsers.add_parser("dashboard", help="Generate an Obsidian-friendly review dashboard")
    dashboard.add_argument("--output", default="docs/review-dashboard.md")
    add_runtime_args(dashboard)
    add_json_arg(dashboard)
    add_common_write_args(dashboard)
    dashboard.set_defaults(func=command_dashboard)

    qmd_readiness = subparsers.add_parser("qmd-readiness", help="Generate a qmd readiness report")
    qmd_readiness.add_argument("--output", default="docs/qmd-readiness.md")
    add_runtime_args(qmd_readiness)
    add_json_arg(qmd_readiness)
    add_common_write_args(qmd_readiness)
    qmd_readiness.set_defaults(func=command_qmd_readiness)

    doctor = subparsers.add_parser("doctor", help="Diagnose config, Profile, Vault, and runtime health")
    add_runtime_args(doctor)
    add_json_arg(doctor)
    doctor.set_defaults(func=command_doctor)

    update = subparsers.add_parser("update", help="Update AgentsKM from its configured GitHub source")
    update.add_argument("--host", choices=["codex", "generic"])
    update.add_argument("--marketplace", default=CODEX_MARKETPLACE)
    update.add_argument("--check", action="store_true")
    add_config_arg(update)
    add_json_arg(update)
    update.set_defaults(func=command_update)

    args = parser.parse_args(argv)
    CONFIG_PATH = get_config_path(getattr(args, "config", None))
    if args.command not in {"configure", "setup", "setup-status", "doctor", "update"}:
        activate_runtime(resolve_runtime(CONFIG_PATH, getattr(args, "profile", None)))
        ensure_vault_root()
    return args.func(args)


def configure_utf8_stdio() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileExistsError, FileNotFoundError, PermissionError, RuntimeError, ValueError) as exc:
        if "--json" in sys.argv:
            emit_json({"ok": False, "error": str(exc), "error_type": exc.__class__.__name__})
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
