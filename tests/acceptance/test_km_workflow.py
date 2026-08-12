#!/usr/bin/env python3
"""End-to-end acceptance tests for the split AgentsKM workflow."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = [sys.executable, "-m", "agentskm_toolkit"]
HTTP_ADAPTER = ROOT / "adapters" / "http" / "km_http.py"
MCP_CONFIG_RENDERER = ROOT / "scripts" / "render_mcp_config.py"
PLUGIN = ROOT / "plugins" / "agentskm-toolkit"
EXPECTED_VERSION = "0.5.3"
CONTRIBUTOR_TOOLS = {
    "km_setup_status", "km_doctor", "km_update", "km_status", "km_pending",
    "km_reminders", "km_search", "km_validate", "km_lint",
    "km_respond_candidate", "km_propose_capture",
}
REVIEWER_TOOLS = CONTRIBUTOR_TOOLS | {"km_review_candidate", "km_dashboard"}
COMPILER_TOOLS = REVIEWER_TOOLS | {"km_promote_candidate", "km_merge_candidate"}
TEST_ROOT: Path
TEST_VAULT: Path
TEST_CONFIG: Path


def main() -> int:
    global TEST_ROOT, TEST_VAULT, TEST_CONFIG
    with tempfile.TemporaryDirectory(prefix="agentskm-acceptance-") as temp:
        TEST_ROOT = Path(temp)
        TEST_VAULT = TEST_ROOT / "vault"
        TEST_CONFIG = TEST_ROOT / "config.json"
        source_override = os.environ.get("AGENTSKM_TEST_FIXTURE_ROOT")
        if source_override:
            source_vault = Path(source_override).resolve()
            if not (source_vault / "000_Inbox").is_dir():
                raise RuntimeError("AGENTSKM_TEST_FIXTURE_ROOT is not an AgentsKM vault")
        else:
            source_vault = TEST_ROOT / "source-vault"
            create_fixture_vault(source_vault)
        shutil.copytree(
            source_vault,
            TEST_VAULT,
            ignore=shutil.ignore_patterns(
                ".git", ".km", ".tmp", ".agents", ".codex", ".obsidian", "__pycache__"
            ),
        )
        os.environ.update(test_env())

        test_setup_bootstrap()
        test_bootstrap_failure_visibility()
        test_default_vault_creation()
        test_setup_profiles()
        test_package_entrypoints()
        if os.environ.get("AGENTSKM_SKIP_UVX") != "1":
            test_uvx_distribution_entrypoint()
        test_legacy_setup_migration()
        test_cli_read_paths()
        test_role_guardrail()
        test_security_guardrails()
        test_frontmatter_escaping()
        test_contributor_response_flow()
        test_review_and_promote_workflow()
        test_merge_workflow()
        test_duplicate_contributors()
        test_dashboard_and_qmd()
        test_http_adapter()
        test_mcp_role_profiles()
        test_mcp_role_change_requires_reconnect()
        test_second_agent_config()
        test_lightweight_plugin()

    print("Acceptance workflow passed.")
    return 0


def create_fixture_vault(path: Path) -> None:
    for relative in ("000_Inbox", "wiki/entities", "wiki/concepts", "wiki/comparisons", "wiki/queries", "raw", "docs"):
        (path / relative).mkdir(parents=True, exist_ok=True)
    (path / "index.md").write_text(
        "# AgentsKM\n\n## Entities\n\n## Concepts\n\n## Comparisons\n\n## Queries\n",
        encoding="utf-8",
    )
    write_fixture_page(
        path / "wiki/queries/lingxing-api-auth.md",
        "API 令牌刷新",
        "query",
        "API 鉴权需要访问令牌，并在过期后安全刷新。",
    )
    write_fixture_page(
        path / "wiki/queries/wsl-windows-chrome-cdp.md",
        "Linux 环境连接宿主浏览器 CDP",
        "query",
        "Linux 环境连接宿主浏览器 CDP：使用宿主地址和受限远程调试端口。",
    )
    write_fixture_page(
        path / "wiki/queries/docsify-api-extraction.md",
        "静态文档 API 提取方法",
        "query",
        "静态文档 API 提取方法包括定位源文件和验证请求参数。",
    )
    write_fixture_page(
        path / "000_Inbox/source-review-needed.md",
        "待补来源候选",
        "note",
        "尚未补充来源。",
        inbox=True,
    )


def write_fixture_page(path: Path, title: str, page_type: str, body: str, *, inbox: bool = False) -> None:
    meta: dict[str, object] = {
        "title": title,
        "created": "2026-01-01",
        "updated": "2026-01-01",
        "type": page_type,
        "tags": ["acceptance"],
    }
    if inbox:
        meta.update({"status": "pending-source-review", "confidence": "medium"})
    else:
        meta.update({"status": "active", "source_refs": ["fixture:acceptance"]})
    frontmatter = "\n".join(
        f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in meta.items()
    )
    path.write_text(f"---\n{frontmatter}\n---\n\n# {title}\n\n{body}\n", encoding="utf-8")


def test_cli_read_paths() -> None:
    status = run_km(["status", "--json"])
    assert status["layers"]["wiki"] >= 1
    search = run_km(["search", "API 令牌刷新", "--limit", "1", "--json"])
    assert search["matches"][0]["path"] == "wiki/queries/lingxing-api-auth.md"
    pending = run_km(["pending", "--json"])
    assert any(item["status"] == "pending-source-review" for item in pending["candidates"])
    reminders = run_km(["reminders", "--json"])
    assert reminders["count"] >= 1
    assert run_km(["validate", "--json"])["ok"] is True
    assert run_km(["lint", "--json"])["ok"] is True


def test_setup_bootstrap() -> None:
    status = run_km(["setup-status", "--profile", "hermes-agent", "--json"])
    assert status["configured"] is False and status["state"] == "config_missing"
    responses = mcp_exchange("hermes-agent", [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ])
    names = {item["name"] for item in responses[1]["result"]["tools"]}
    assert {"km_setup_status", "km_doctor", "km_update", "km_propose_capture"} <= names
    assert "km_promote_candidate" not in names
    configured = run_km(["setup-status", "--profile", "hermes-agent", "--json"])
    assert configured["configured"] is True
    assert Path(configured["vault_path"]).resolve() == TEST_VAULT.resolve()


def test_bootstrap_failure_visibility() -> None:
    root = TEST_ROOT / "bootstrap-failure"
    blocked_vault = root / "vault"
    blocked_vault.mkdir(parents=True)
    (blocked_vault / "unrelated.txt").write_text("not a Vault", encoding="utf-8")
    config = root / "config.json"
    responses = mcp_exchange("codex", [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "km_setup_status", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "km_setup_instructions", "arguments": {}}},
    ], config_path=config)
    names = {item["name"] for item in responses[1]["result"]["tools"]}
    assert names == {"km_setup_status", "km_doctor", "km_update", "km_setup_instructions"}
    status = responses[2]["result"]["structuredContent"]
    assert status["session_configured"] is False
    assert status["bootstrap_error"]["state"] == "bootstrap_failed"
    assert "non-empty non-AgentsKM" in status["bootstrap_error"]["error"]
    command = responses[3]["result"]["structuredContent"]["cli_command"]
    assert command[command.index("--role") + 1] == "compiler"
    assert "--confirm-compiler" in command


def test_default_vault_creation() -> None:
    fresh_config = TEST_ROOT / "fresh-install" / "config.json"
    responses = mcp_exchange("cursor", [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ], config_path=fresh_config)
    names = {item["name"] for item in responses[1]["result"]["tools"]}
    assert "km_propose_capture" in names and "km_promote_candidate" not in names
    saved = json.loads(fresh_config.read_text(encoding="utf-8"))
    vault = Path(saved["vaults"]["main"]["path"])
    assert vault == (fresh_config.parent / "vault").resolve()
    assert (vault / "README.md").exists()
    assert (vault / "000_Inbox").is_dir() and (vault / "wiki").is_dir()


def test_setup_profiles() -> None:
    hermes_args = [
        "setup",
        "--profile", "hermes-agent",
        "--host", "hermes",
        "--actor-id", "hermes-agent",
        "--role", "contributor",
        "--vault-name", "main",
        "--vault", str(TEST_VAULT),
        "--json",
    ]
    configured = run_km(hermes_args)
    assert configured["changed"] is False and configured["restart_required"] is False
    assert configured["reconnect_required"] is True
    repeated = run_km(hermes_args)
    assert repeated["state"] == "already_configured" and repeated["changed"] is False

    blocked = run_process([
        *CLI,
        "setup",
        "--profile", "codex",
        "--host", "codex",
        "--role", "compiler",
        "--vault-name", "main",
        "--config", str(TEST_CONFIG),
        "--json",
    ])
    assert blocked.returncode != 0
    assert "--confirm-compiler" in json.loads(blocked.stdout)["error"]

    codex = run_km([
        "setup",
        "--profile", "codex",
        "--host", "codex",
        "--actor-id", "codex",
        "--role", "compiler",
        "--vault-name", "main",
        "--confirm-compiler",
        "--json",
    ])
    assert codex["role"] == "compiler"
    codex_repeated = run_km([
        "setup",
        "--profile", "codex",
        "--host", "codex",
        "--actor-id", "codex",
        "--role", "compiler",
        "--vault-name", "main",
        "--json",
    ])
    assert codex_repeated["state"] == "already_configured"
    reviewer = run_km([
        "setup",
        "--profile", "km-reviewer",
        "--host", "generic",
        "--actor-id", "km-reviewer",
        "--role", "reviewer",
        "--vault-name", "main",
        "--json",
    ])
    assert reviewer["role"] == "reviewer"

    saved = json.loads(TEST_CONFIG.read_text(encoding="utf-8"))
    assert saved["schema_version"] == 1
    assert Path(saved["vaults"]["main"]["path"]).resolve() == TEST_VAULT.resolve()
    assert saved["profiles"]["hermes-agent"]["role"] == "contributor"
    assert saved["profiles"]["codex"]["role"] == "compiler"
    doctor = run_km(["doctor", "--profile", "codex", "--json"])
    assert doctor["ok"] is True
    assert doctor["toolkit_version"] == EXPECTED_VERSION
    assert doctor["configuration_source"] == "config_file"


def test_package_entrypoints() -> None:
    help_result = run_process([*CLI, "--help"])
    assert help_result.returncode == 0
    for command in ("setup-status", "pending", "reminders", "validate", "lint", "dashboard", "qmd-readiness", "update", "mcp"):
        assert command in help_result.stdout
    subcommand_help = run_process([*CLI, "propose", "--help"])
    assert subcommand_help.returncode == 0
    assert "Exit codes:" in subcommand_help.stdout
    assert "(default:" in subcommand_help.stdout
    invalid = run_process([*CLI, "propose", "--unknown-option", "value", "--json"])
    assert invalid.returncode == 2
    invalid_payload = json.loads(invalid.stdout)
    assert invalid_payload["error_type"] == "ArgumentError"
    assert invalid_payload["next_action"] == "run_command_help"

    version = run_process([sys.executable, "-m", "agentskm_toolkit", "--version"])
    assert version.returncode == 0, version.stderr
    assert version.stdout.strip() == EXPECTED_VERSION

    doctor = run_process([
        sys.executable,
        "-m", "agentskm_toolkit",
        "doctor",
        "--profile", "codex",
        "--config", str(TEST_CONFIG),
        "--json",
    ])
    assert doctor.returncode == 0, doctor.stdout or doctor.stderr
    assert json.loads(doctor.stdout)["toolkit_version"] == EXPECTED_VERSION

    input_text = "\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
        "",
    ])
    mcp = run_process([
        sys.executable,
        "-m", "agentskm_toolkit",
        "mcp",
        "--profile", "hermes-agent",
        "--host", "hermes",
        "--bootstrap-role", "contributor",
        "--config", str(TEST_CONFIG),
    ], input_text=input_text)
    assert mcp.returncode == 0, mcp.stderr
    responses = [json.loads(line) for line in mcp.stdout.splitlines() if line.strip()]
    assert responses[0]["result"]["serverInfo"]["version"] == EXPECTED_VERSION
    names = {item["name"] for item in responses[1]["result"]["tools"]}
    assert "km_respond_candidate" in names
    assert "km_promote_candidate" not in names


def test_uvx_distribution_entrypoint() -> None:
    if not shutil.which("uvx"):
        raise RuntimeError("uvx is required for productization acceptance")

    version = run_uvx_process(["uvx", "--from", str(ROOT), "agentskm", "--version"])
    assert version.returncode == 0, version.stdout or version.stderr
    assert version.stdout.strip().splitlines()[0] == EXPECTED_VERSION

    wrong_executable = run_uvx_process(["uvx", "--from", str(ROOT), "agentskm-toolkit", "--version"])
    assert wrong_executable.returncode != 0
    assert "An executable named" in wrong_executable.stderr

    uvx_config = TEST_ROOT / "uvx-config.json"
    input_text = "\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
        json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "km_propose_capture",
                "arguments": {
                    "title": "uvx local acceptance capture",
                    "value_reason": "Verify uvx package MCP can write Inbox through contributor role",
                    "body": "This candidate is created by isolated uvx acceptance.",
                    "source_session": "uvx-acceptance",
                },
            },
        }),
        json.dumps({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "km_promote_candidate",
                "arguments": {
                    "candidate": "kmc-does-not-matter",
                    "approved_by": "hermes-agent",
                    "scope": "acceptance",
                    "dry_run": True,
                },
            },
        }),
        "",
    ])
    mcp = run_uvx_process([
        "uvx",
        "--from", str(ROOT),
        "agentskm",
        "mcp",
        "--profile", "hermes-agent",
        "--host", "hermes",
        "--bootstrap-role", "contributor",
        "--config", str(uvx_config),
    ], input_text=input_text)
    assert mcp.returncode == 0, mcp.stderr
    responses = [json.loads(line) for line in mcp.stdout.splitlines() if line.strip()]
    names = {item["name"] for item in responses[1]["result"]["tools"]}
    assert "km_propose_capture" in names and "km_promote_candidate" not in names
    assert responses[2]["result"]["structuredContent"]["created"] is True
    assert responses[3]["id"] == 4
    assert responses[3]["result"]["isError"] is True
    assert "Compiler role is required" in responses[3]["result"]["structuredContent"]["error"]
    assert (uvx_config.parent / "vault" / "000_Inbox" / "uvx-local-acceptance-capture.md").exists()


def test_legacy_setup_migration() -> None:
    legacy_config = TEST_ROOT / "legacy-config.json"
    legacy_config.write_text(
        json.dumps({"vault": str(TEST_VAULT)}, ensure_ascii=False),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            *CLI,
            "setup",
            "--profile", "hermes-agent",
            "--host", "hermes",
            "--role", "contributor",
            "--vault-name", "main",
            "--config", str(legacy_config),
            "--json",
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stdout or proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["migrated_legacy_config"] is True
    assert legacy_config.with_suffix(".json.v0.bak").exists()
    migrated = json.loads(legacy_config.read_text(encoding="utf-8"))
    assert migrated["schema_version"] == 1
    assert migrated["profiles"]["default"]["role"] == "contributor"


def test_role_guardrail() -> None:
    proc = run_process([
        *CLI,
        "promote",
        "000_Inbox/ai-agent-platform-comparison-2025.md",
        "--target", "wiki/comparisons/blocked.md",
        "--approved-by", "user",
        "--scope", "acceptance",
        "--profile", "hermes-agent",
        "--config", str(TEST_CONFIG),
        "--dry-run",
        "--json",
    ])
    assert proc.returncode != 0
    assert "requires role=compiler" in json.loads(proc.stdout)["error"]


def test_security_guardrails() -> None:
    override = run_process([
        *CLI, "dashboard",
        "--profile", "hermes-agent",
        "--config", str(TEST_CONFIG),
        "--actor-role", "reviewer",
        "--dry-run",
        "--json",
    ])
    assert override.returncode != 0
    override_payload = json.loads(override.stdout)
    assert override_payload["error_type"] == "ArgumentError"
    assert "unrecognized arguments: --actor-role" in override_payload["error"]

    contributor_report = run_process([
        *CLI, "qmd-readiness",
        "--profile", "hermes-agent",
        "--config", str(TEST_CONFIG),
        "--output", "docs/contributor.md",
        "--dry-run",
        "--json",
    ])
    assert contributor_report.returncode != 0
    assert "requires role=reviewer" in json.loads(contributor_report.stdout)["error"]

    escaped_report = run_process([
        *CLI, "dashboard",
        "--profile", "km-reviewer",
        "--config", str(TEST_CONFIG),
        "--output", "wiki/concepts/unauthorized.md",
        "--dry-run",
        "--json",
    ])
    assert escaped_report.returncode != 0
    assert "inside docs/" in json.loads(escaped_report.stdout)["error"]

    proposed = run_km([
        "propose", "--profile", "hermes-agent",
        "--title", "Traversal Guardrail",
        "--value-reason", "验证 Wiki 路径边界",
        "--source-ref", "conversation:path-guard",
        "--json",
    ])
    candidate = proposed["candidate_path"]
    run_km([
        "review", candidate,
        "--profile", "km-reviewer",
        "--decision", "approve",
        "--reviewed-by", "acceptance-user",
        "--json",
    ])
    traversal = run_process([
        *CLI, "promote", candidate,
        "--profile", "codex",
        "--config", str(TEST_CONFIG),
        "--target", "wiki/concepts/../../docs/escaped.md",
        "--approved-by", "acceptance-user",
        "--scope", "path audit",
        "--dry-run",
        "--json",
    ])
    assert traversal.returncode != 0
    traversal_payload = json.loads(traversal.stdout)
    assert traversal_payload["blocker_code"] == "invalid_wiki_target"
    assert traversal_payload["example"] == "wiki/concepts/project-state-space.md"

    secret = run_process([
        *CLI, "propose",
        "--profile", "hermes-agent",
        "--config", str(TEST_CONFIG),
        "--title", "Secret must not persist",
        "--value-reason", "security",
        "--sensitivity", "secret",
        "--json",
    ])
    assert secret.returncode != 0

    invalid_guide_target = run_process([
        *CLI, "propose",
        "--profile", "hermes-agent",
        "--config", str(TEST_CONFIG),
        "--title", "Guide target category guard",
        "--type", "guide",
        "--suggested-target", "wiki/guides/unsupported.md",
        "--value-reason", "验证候选阶段拒绝不受支持的 Wiki 目录",
        "--source-session", "guide-target-guard",
        "--json",
    ])
    assert invalid_guide_target.returncode != 0
    invalid_target_payload = json.loads(invalid_guide_target.stdout)
    assert invalid_target_payload["blocker_code"] == "invalid_wiki_target"
    assert invalid_target_payload["next_action"] == "provide_valid_wiki_target_or_omit_suggested_target"
    assert invalid_target_payload["accepted_format"] == "wiki/<entities|concepts|comparisons|queries>/<slug>.md"
    assert invalid_target_payload["example"] == "wiki/concepts/project-state-space.md"
    assert "wiki/queries" in invalid_target_payload["allowed_categories"]

    missing_wiki_prefix = run_process([
        *CLI, "propose",
        "--profile", "hermes-agent",
        "--config", str(TEST_CONFIG),
        "--title", "Missing Wiki Prefix Guard",
        "--type", "concept",
        "--suggested-target", "concepts/project-state-space.md",
        "--value-reason", "验证错误信息提供完整 target 格式",
        "--source-session", "missing-wiki-prefix-guard",
        "--json",
    ])
    assert missing_wiki_prefix.returncode != 0
    missing_prefix_payload = json.loads(missing_wiki_prefix.stdout)
    assert missing_prefix_payload["blocker_code"] == "invalid_wiki_target"
    assert "including the wiki/ prefix" in missing_prefix_payload["error"]
    assert missing_prefix_payload["example"] == "wiki/concepts/project-state-space.md"

    inbox_before = {path.name for path in (TEST_VAULT / "000_Inbox").glob("*.md")}
    fake_secret = "sk-" + "A" * 32
    body_secret = run_process([
        *CLI, "propose",
        "--profile", "hermes-agent",
        "--config", str(TEST_CONFIG),
        "--title", "Body secret must not persist",
        "--value-reason", "验证正文敏感内容拦截",
        "--body", f"Do not store this credential: {fake_secret}",
        "--source-session", "body-secret-guard",
        "--json",
    ])
    assert body_secret.returncode != 0
    body_secret_payload = json.loads(body_secret.stdout)
    assert body_secret_payload["blocker_code"] == "sensitive_content_blocked"
    assert "candidate was not written" in body_secret_payload["error"]
    assert {path.name for path in (TEST_VAULT / "000_Inbox").glob("*.md")} == inbox_before
    log_text = (TEST_VAULT / "log.md").read_text(encoding="utf-8") if (TEST_VAULT / "log.md").exists() else ""
    assert fake_secret not in log_text

    ordinary_token_text = run_km([
        "propose",
        "--profile", "hermes-agent",
        "--title", "Token refresh terminology is safe",
        "--value-reason", "验证普通 token refresh 技术描述不会误报",
        "--body", "Document the token refresh flow without storing credential values.",
        "--source-session", "ordinary-token-refresh",
        "--json",
    ])
    assert ordinary_token_text["created"] is True
    assert ordinary_token_text["operation"] == "create_inbox_candidate"


def test_frontmatter_escaping() -> None:
    title = "Frontmatter 安全\ninjected: false"
    source_ref = "conversation:frontmatter,segment"
    proposed = run_km([
        "propose", "--profile", "hermes-agent",
        "--title", title,
        "--value-reason", "验证换行和逗号不会破坏元数据",
        "--source-ref", source_ref,
        "--json",
    ])
    path = TEST_VAULT / proposed["candidate_path"]
    text = path.read_text(encoding="utf-8")
    assert "\\ninjected: false" in text
    candidate = next(
        item for item in run_km(["pending", "--profile", "hermes-agent", "--json"])["candidates"]
        if item["path"] == proposed["candidate_path"]
    )
    assert candidate["title"] == title
    assert candidate["source_refs"] == [source_ref]


def test_contributor_response_flow() -> None:
    proposed = run_km([
        "propose",
        "--title", "Hermes Contributor Response",
        "--type", "concept",
        "--tags", "agentskm,hermes,permissions",
        "--suggested-target", "wiki/concepts/hermes-contributor-response.md",
        "--value-reason", "验证 contributor 可记录用户交互但不能批准或写 Wiki",
        "--body", "Hermes 应能记录提醒和用户沉淀意图，后续由 reviewer/compiler 接棒。",
        "--agent-id", "hermes-agent",
        "--source-session", "acceptance-respond",
        "--profile", "hermes-agent",
        "--json",
    ])
    candidate = proposed["candidate_path"]
    text = (TEST_VAULT / candidate).read_text(encoding="utf-8")
    assert proposed["status"] == "pending"
    assert "conversation:acceptance-respond" in text

    reminded = run_km([
        "respond", candidate,
        "--decision", "remind",
        "--agent-id", "hermes-agent",
        "--profile", "hermes-agent",
        "--json",
    ])
    assert reminded["status"] == "reminded"

    captured = run_km([
        "respond", candidate,
        "--decision", "capture",
        "--responded-by", "acceptance-user",
        "--reason", "用户选择沉淀",
        "--profile", "hermes-agent",
        "--json",
    ])
    assert captured["status"] == "reminded"
    assert captured["intent_status"] == "capture_requested"
    assert captured["candidate_path"] == candidate
    assert captured["next_action"] == "await_review"
    assert captured["next_required_role"] == "reviewer-or-compiler"
    text = (TEST_VAULT / candidate).read_text(encoding="utf-8")
    assert 'user_decision: "capture"' in text
    assert 'response_actor_role: "contributor"' in text
    assert 'next_required_role: "reviewer-or-compiler"' in text

    snoozed = run_km([
        "respond", candidate,
        "--decision", "snooze",
        "--responded-by", "acceptance-user",
        "--profile", "hermes-agent",
        "--json",
    ])
    assert snoozed["status"] == "snoozed"
    assert snoozed["snoozed_until"] == (date.today() + timedelta(days=7)).isoformat()
    assert snoozed["next_action"] == "wait_until_snoozed_until"

    proc = run_process([
        *CLI,
        "respond", candidate,
        "--decision", "approve",
        "--profile", "hermes-agent",
        "--config", str(TEST_CONFIG),
        "--json",
    ])
    assert proc.returncode != 0


def test_review_and_promote_workflow() -> None:
    proposed = run_km([
        "propose",
        "--title", "验收知识捕获流程",
        "--type", "concept",
        "--tags", "methodology,workflow",
        "--source-ref", "conversation:acceptance-promote",
        "--suggested-target", "wiki/concepts/acceptance-capture-workflow.md",
        "--value-reason", "验证跨 Agent 知识沉淀闭环",
        "--body", "经过验证的候选应先审核，再进入正式 Wiki。",
        "--agent-id", "codex-acceptance",
        "--source-session", "acceptance-promote",
        "--profile", "hermes-agent",
        "--json",
    ])
    candidate = proposed["candidate_path"]
    assert any(item["path"] == candidate for item in run_km(["reminders", "--json"])["candidates"])

    reminded = run_km([
        "review", candidate,
        "--decision", "remind",
        "--agent-id", "codex-acceptance",
        "--profile", "km-reviewer",
        "--json",
    ])
    assert reminded["status"] == "reminded"
    assert not any(item["path"] == candidate for item in run_km(["reminders", "--json"])["candidates"])

    snoozed = run_km([
        "review", candidate,
        "--decision", "snooze",
        "--until", date.today().isoformat(),
        "--reviewed-by", "acceptance-user",
        "--profile", "km-reviewer",
        "--json",
    ])
    assert snoozed["status"] == "snoozed"
    assert snoozed["snoozed_until"] == date.today().isoformat()
    assert any(item["path"] == candidate for item in run_km(["reminders", "--json"])["candidates"])

    approved = run_km([
        "review", candidate,
        "--decision", "approve",
        "--reviewed-by", "acceptance-user",
        "--reason", "用户选择沉淀",
        "--profile", "km-reviewer",
        "--json",
    ])
    assert approved["status"] == "approved"

    promoted = run_km([
        "promote", candidate,
        "--target", "wiki/concepts/acceptance-capture-workflow.md",
        "--approved-by", "acceptance-user",
        "--scope", "用户批准验收候选毕业",
        "--profile", "codex",
        "--json",
    ])
    assert promoted["promoted"] is True
    assert promoted["status"] == "graduated"
    assert promoted["operation"] == "create_wiki_page"
    assert promoted["next_action"] == "complete"
    assert (TEST_VAULT / promoted["target"]).exists()
    assert "acceptance-capture-workflow.md" in (TEST_VAULT / "index.md").read_text(encoding="utf-8")
    assert 'status: "graduated"' in (TEST_VAULT / candidate).read_text(encoding="utf-8")


def test_merge_workflow() -> None:
    proposed = run_km([
        "propose",
        "--title", "API 令牌刷新增量边界",
        "--type", "query",
        "--tags", "api,auth,lingxing",
        "--source-ref", "conversation:acceptance-merge",
        "--suggested-action", "merge",
        "--suggested-target", "wiki/queries/lingxing-api-auth.md",
        "--value-reason", "补充正式页的验收边界",
        "--body", "验收补充：调用方应在刷新令牌后重放一次失败请求。",
        "--profile", "hermes-agent",
        "--json",
    ])
    candidate = proposed["candidate_path"]
    run_km([
        "review", candidate,
        "--decision", "approve",
        "--reviewed-by", "acceptance-user",
        "--profile", "km-reviewer",
        "--json",
    ])
    merged = run_km([
        "merge", candidate,
        "--target", "wiki/queries/lingxing-api-auth.md",
        "--approved-by", "acceptance-user",
        "--scope", "用户批准合并验收边界",
        "--profile", "codex",
        "--json",
    ])
    assert merged["merged"] is True
    assert merged["status"] == "merged"
    assert merged["operation"] == "merge_wiki_page"
    assert merged["next_action"] == "complete"
    target_body = (TEST_VAULT / merged["target"]).read_text(encoding="utf-8")
    assert "调用方应在刷新令牌后重放一次失败请求" in target_body
    assert 'status: "merged"' in (TEST_VAULT / candidate).read_text(encoding="utf-8")


def test_duplicate_contributors() -> None:
    common = [
        "propose",
        "--title", "多 Agent 重复候选验收",
        "--type", "concept",
        "--tags", "ai-agent,workflow",
        "--suggested-target", "wiki/concepts/multi-agent-duplicate.md",
        "--value-reason", "验证多 Agent 去重并保留来源",
        "--body", "相同主题应合并贡献者和来源。",
        "--profile", "hermes-agent",
        "--json",
    ]
    first = run_km([*common, "--source-ref", "conversation:agent-a", "--agent-id", "agent-a", "--source-session", "agent-a-session"])
    second = run_km([*common, "--source-ref", "conversation:agent-b", "--agent-id", "agent-b", "--source-session", "agent-b-session"])
    assert second["duplicate"] is True
    body = (TEST_VAULT / first["candidate_path"]).read_text(encoding="utf-8")
    assert "conversation:agent-a" in body and "conversation:agent-b" in body
    assert "agent-a" in body and "agent-b" in body


def test_dashboard_and_qmd() -> None:
    dashboard = run_km(["dashboard", "--profile", "km-reviewer", "--json"])
    assert (TEST_VAULT / dashboard["output"]).exists()
    qmd = run_km(["qmd-readiness", "--profile", "km-reviewer", "--json"])
    assert qmd["ready"] is False
    assert qmd["top5_hit_rate"] >= 0.9
    assert qmd["queries"]
    assert all(item["query"] for item in qmd["queries"])


def test_http_adapter() -> None:
    mod = import_module(HTTP_ADAPTER, "km_http_acceptance")
    mod.PROFILE = "codex"
    mod.CONFIG_PATH = str(TEST_CONFIG)
    mod.HTTP_TOKEN = "acceptance-token"
    server = ThreadingHTTPServer(("127.0.0.1", 0), mod.KMHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        health_status, health = http_get(port, "/health")
        assert health_status == 200 and health["ok"] is True
        search_route = "/search?" + urllib.parse.urlencode({"q": "API 令牌刷新", "limit": "1"})
        unauthorized_read, _ = http_get(port, search_route)
        assert unauthorized_read == 401
        search_status, search = http_get(port, search_route, token="acceptance-token")
        assert search_status == 200 and search["matches"]
        unauthorized_status, _ = http_post(port, "/propose", {"title": "blocked", "value_reason": "blocked"})
        assert unauthorized_status == 401
        authorized_status, payload = http_post(
            port,
            "/propose",
            {
                "title": "HTTP dry run",
                "value_reason": "验证 HTTP token",
                "source_refs": ["conversation:http"],
                "dry_run": True,
            },
            token="acceptance-token",
        )
        assert authorized_status == 200 and payload["dry_run"] is True
    finally:
        server.shutdown()
        server.server_close()


def test_mcp_role_profiles() -> None:
    contributor = mcp_exchange("hermes-agent", [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {
                "name": "km_propose_capture",
                "arguments": {
                    "title": "MCP body secret guard",
                    "value_reason": "验证 MCP 敏感正文错误结构",
                    "body": "credential: " + "sk-" + "B" * 32,
                    "source_session": "mcp-body-secret",
                },
            },
        },
        {
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {
                "name": "km_promote_candidate",
                "arguments": {
                    "candidate": "000_Inbox/not-used.md",
                    "approved_by": "acceptance-user",
                    "scope": "permission response",
                },
            },
        },
    ])
    contributor_names = {item["name"] for item in contributor[1]["result"]["tools"]}
    assert contributor_names == CONTRIBUTOR_TOOLS
    sensitive_error = contributor[2]["result"]["structuredContent"]
    assert contributor[2]["result"]["isError"] is True
    assert sensitive_error["blocker_code"] == "sensitive_content_blocked"
    role_error = contributor[3]["result"]["structuredContent"]
    assert contributor[3]["result"]["isError"] is True
    assert role_error["blocker_code"] == "role_required"
    assert role_error["next_required_role"] == "compiler"

    reviewer = mcp_exchange("km-reviewer", [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ])
    reviewer_names = {item["name"] for item in reviewer[1]["result"]["tools"]}
    assert reviewer_names == REVIEWER_TOOLS

    compiler = mcp_exchange("codex", [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "km_search", "arguments": {"query": "API 令牌刷新", "limit": 1}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "km_propose_capture", "arguments": {"title": "MCP 来源验收", "value_reason": "验证来源身份", "dry_run": True}}},
    ])
    compiler_tools = compiler[1]["result"]["tools"]
    compiler_names = {item["name"] for item in compiler_tools}
    assert compiler_names == COMPILER_TOOLS
    capture_tool = next(item for item in compiler_tools if item["name"] == "km_propose_capture")
    capture_type = capture_tool["inputSchema"]["properties"]["type"]
    assert capture_type["enum"] == [
        "comparison", "concept", "entity", "guide", "note", "query", "summary",
    ]
    target_description = capture_tool["inputSchema"]["properties"]["suggested_target"]["description"]
    assert "include the wiki/ prefix" in target_description
    assert "wiki/concepts/project-state-space.md" in target_description
    assert compiler[2]["result"]["structuredContent"]["matches"][0]["layer"] == "wiki"
    candidate = compiler[3]["result"]["structuredContent"]["candidate"]
    assert candidate["agent_id"] == "codex"
    assert candidate["source_tool"] == "codex-mcp"


def test_mcp_role_change_requires_reconnect() -> None:
    config = TEST_ROOT / "reconnect-config.json"
    payload = json.loads(TEST_CONFIG.read_text(encoding="utf-8"))
    payload["default_profile"] = "hermes-agent"
    config.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    env = os.environ.copy()
    env.update(test_env())
    proc = subprocess.Popen(
        [*CLI, "mcp", "--profile", "hermes-agent", "--host", "hermes", "--config", str(config)],
        cwd=ROOT,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    assert proc.stdin and proc.stdout

    def exchange(message: dict) -> dict:
        proc.stdin.write(json.dumps(message) + "\n")
        proc.stdin.flush()
        return json.loads(proc.stdout.readline())

    exchange({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    before = exchange({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    before_names = {item["name"] for item in before["result"]["tools"]}
    assert "km_review_candidate" not in before_names

    payload["profiles"]["hermes-agent"]["role"] = "reviewer"
    config.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    after = exchange({"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}})
    after_names = {item["name"] for item in after["result"]["tools"]}
    assert after_names == before_names
    status = exchange({
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"name": "km_setup_status", "arguments": {}},
    })
    session = status["result"]["structuredContent"]
    assert session["session_role"] == "contributor"
    assert session["reconnect_required"] is True
    proc.stdin.close()
    assert proc.wait(timeout=10) == 0


def test_lightweight_plugin() -> None:
    assert not (PLUGIN / "tools").exists()
    assert not (PLUGIN / "adapters").exists()
    command_names = {path.name for path in (PLUGIN / "commands").glob("*.md")}
    assert command_names == {"km-doctor.md", "km-capture.md", "km-search.md"}
    for command in command_names:
        text = (PLUGIN / "commands" / command).read_text(encoding="utf-8")
        assert "AgentsKM MCP" in text
    assert not (PLUGIN / "README.md").exists()
    skill_path = PLUGIN / "skills" / "agentskm" / "SKILL.md"
    assert skill_path.exists()
    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["version"] == EXPECTED_VERSION
    server = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["agentskm"]
    assert server["command"] == "uvx"
    assert server["args"][:4] == [
        "--from",
        f"agentskm-toolkit=={EXPECTED_VERSION}",
        "agentskm",
        "mcp",
    ]
    assert server["args"][server["args"].index("--profile") + 1] == "codex"
    assert server["args"][server["args"].index("--bootstrap-role") + 1] == "compiler"
    skill_text = skill_path.read_text(encoding="utf-8")
    frontmatter = skill_text.split("---", 2)[1]
    keys = {line.split(":", 1)[0] for line in frontmatter.strip().splitlines()}
    assert keys == {"name", "description"}
    assert len(skill_text.splitlines()) <= 100
    for reference in ("capture-workflow.md", "setup-and-profiles.md", "roles-and-approval.md"):
        assert f"references/{reference}" in skill_text

    if os.environ.get("AGENTSKM_SKIP_UVX") != "1":
        local_args = list(server["args"])
        local_args[local_args.index("--from") + 1] = str(ROOT)
        input_text = "\n".join([
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
            "",
        ])
        proc = run_uvx_process([server["command"], *local_args, "--config", str(TEST_CONFIG)], input_text)
        assert proc.returncode == 0, proc.stderr
        responses = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
        names = {item["name"] for item in responses[1]["result"]["tools"]}
        assert "km_setup_status" in names and "km_promote_candidate" in names
        assert "km_configure_vault" not in names


def test_second_agent_config() -> None:
    output = TEST_ROOT / "claude.mcp.json"
    proc = run_process([
        sys.executable,
        str(MCP_CONFIG_RENDERER),
        "--agent", "hermes",
        "--profile", "hermes-agent",
        "--config", str(TEST_CONFIG),
        "--runtime", "uvx",
        "--output", str(output),
    ])
    assert proc.returncode == 0, proc.stderr
    server = json.loads(output.read_text(encoding="utf-8"))["mcpServers"]["agentskm"]
    assert server["command"] == "uvx"
    assert server["args"][:4] == ["--from", f"agentskm-toolkit=={EXPECTED_VERSION}", "agentskm", "mcp"]
    assert server["args"][server["args"].index("--profile") + 1] == "hermes-agent"


def test_env() -> dict[str, str]:
    existing = os.environ.get("PYTHONPATH", "")
    src_path = str(ROOT / "src")
    pythonpath = src_path if not existing else src_path + os.pathsep + existing
    return {
        "PYTHONUTF8": "1",
        "PYTHONPATH": pythonpath,
    }

def run_km(args: list[str]) -> dict:
    contextual = list(args)
    if "--config" not in contextual:
        contextual.extend(["--config", str(TEST_CONFIG)])
    runtime_commands = {
        "status", "pending", "reminders", "search", "validate", "lint", "propose",
        "respond", "review", "promote", "merge", "dashboard", "qmd-readiness", "doctor",
    }
    if contextual[0] in runtime_commands and "--profile" not in contextual:
        contextual.extend(["--profile", "codex"])
    proc = run_process([*CLI, *contextual])
    assert proc.returncode == 0, proc.stdout or proc.stderr
    return json.loads(proc.stdout)


def run_process(args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(test_env())
    return subprocess.run(
        args,
        cwd=ROOT,
        input=input_text,
        text=True,
        encoding="utf-8",
        env=env,
        capture_output=True,
    )


def run_uvx_process(args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["UV_CACHE_DIR"] = str(TEST_ROOT / "uv-cache")
    env["UV_TOOL_DIR"] = str(TEST_ROOT / "uv-tools")
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        args,
        cwd=ROOT,
        input=input_text,
        text=True,
        encoding="utf-8",
        env=env,
        capture_output=True,
    )


def mcp_exchange(
    profile: str,
    messages: list[dict],
    config_path: Path | None = None,
) -> list[dict]:
    input_text = "\n".join(json.dumps(item, ensure_ascii=True) for item in messages) + "\n"
    host = "codex" if profile == "codex" else profile.removesuffix("-agent")
    role = "compiler" if profile == "codex" else "contributor"
    proc = run_process([
        *CLI,
        "mcp",
        "--profile", profile,
        "--host", host,
        "--bootstrap-role", role,
        "--config", str(config_path or TEST_CONFIG),
    ], input_text=input_text)
    assert proc.returncode == 0, proc.stderr
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def http_get(port: int, route: str, token: str = "") -> tuple[int, dict]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    request = urllib.request.Request(f"http://127.0.0.1:{port}{route}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def http_post(port: int, route: str, payload: dict, token: str = "") -> tuple[int, dict]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{route}",
        data=data,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
