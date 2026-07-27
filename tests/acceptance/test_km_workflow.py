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
from datetime import date
from http.server import ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
KM = ROOT / "tools" / "km-cli" / "km.py"
HTTP_ADAPTER = ROOT / "adapters" / "http" / "km_http.py"
MCP_ADAPTER = ROOT / "adapters" / "mcp" / "km_mcp.py"
MCP_CONFIG_RENDERER = ROOT / "scripts" / "render_mcp_config.py"
PLUGIN = ROOT / "plugins" / "agentskm-toolkit"
SOURCE_VAULT = Path(os.environ.get("AGENTSKM_DATA_ROOT", ROOT)).resolve()
TEST_ROOT: Path
TEST_VAULT: Path
TEST_CONFIG: Path


def main() -> int:
    global TEST_ROOT, TEST_VAULT, TEST_CONFIG
    if not (SOURCE_VAULT / "000_Inbox").is_dir():
        raise RuntimeError("Set AGENTSKM_DATA_ROOT to an AgentsKM vault before running acceptance tests")

    with tempfile.TemporaryDirectory(prefix="agentskm-acceptance-") as temp:
        TEST_ROOT = Path(temp)
        TEST_VAULT = TEST_ROOT / "vault"
        TEST_CONFIG = TEST_ROOT / "config.json"
        shutil.copytree(
            SOURCE_VAULT,
            TEST_VAULT,
            ignore=shutil.ignore_patterns(".git", ".km", "__pycache__"),
        )
        os.environ.update(test_env())

        test_cli_read_paths()
        test_configure()
        test_role_guardrail()
        test_review_and_promote_workflow()
        test_merge_workflow()
        test_duplicate_contributors()
        test_dashboard_and_qmd()
        test_http_adapter()
        test_mcp_role_profiles()
        test_second_agent_config()
        test_self_contained_plugin()

    print("Acceptance workflow passed.")
    return 0


def test_cli_read_paths() -> None:
    status = run_km(["status", "--json"])
    assert status["layers"]["wiki"] >= 1
    search = run_km(["search", "领星 API 鉴权", "--limit", "1", "--json"])
    assert search["matches"][0]["path"] == "wiki/queries/lingxing-api-auth.md"
    pending = run_km(["pending", "--json"])
    assert any(item["status"] == "pending-source-review" for item in pending["candidates"])
    reminders = run_km(["reminders", "--json"])
    assert reminders["count"] >= 1
    assert run_km(["validate", "--json"])["ok"] is True
    assert run_km(["lint", "--json"])["ok"] is True


def test_configure() -> None:
    payload = run_km(["configure", "--vault", str(TEST_VAULT), "--json"])
    assert payload["configured"] is True
    saved = json.loads(TEST_CONFIG.read_text(encoding="utf-8"))
    assert Path(saved["vault"]).resolve() == TEST_VAULT.resolve()


def test_role_guardrail() -> None:
    proc = run_process([
        sys.executable,
        str(KM),
        "promote",
        "000_Inbox/ai-agent-platform-comparison-2025.md",
        "--target", "wiki/comparisons/blocked.md",
        "--approved-by", "user",
        "--scope", "acceptance",
        "--actor-role", "contributor",
        "--dry-run",
        "--json",
    ])
    assert proc.returncode != 0
    assert "requires role=compiler" in json.loads(proc.stdout)["error"]


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
        "--actor-role", "contributor",
        "--json",
    ])
    candidate = proposed["candidate_path"]
    assert any(item["path"] == candidate for item in run_km(["reminders", "--json"])["candidates"])

    reminded = run_km([
        "review", candidate,
        "--decision", "remind",
        "--agent-id", "codex-acceptance",
        "--actor-role", "reviewer",
        "--json",
    ])
    assert reminded["status"] == "reminded"
    assert not any(item["path"] == candidate for item in run_km(["reminders", "--json"])["candidates"])

    snoozed = run_km([
        "review", candidate,
        "--decision", "snooze",
        "--until", date.today().isoformat(),
        "--reviewed-by", "acceptance-user",
        "--actor-role", "reviewer",
        "--json",
    ])
    assert snoozed["status"] == "snoozed"
    assert any(item["path"] == candidate for item in run_km(["reminders", "--json"])["candidates"])

    approved = run_km([
        "review", candidate,
        "--decision", "approve",
        "--reviewed-by", "acceptance-user",
        "--reason", "用户选择沉淀",
        "--actor-role", "reviewer",
        "--json",
    ])
    assert approved["status"] == "approved"

    promoted = run_km([
        "promote", candidate,
        "--target", "wiki/concepts/acceptance-capture-workflow.md",
        "--approved-by", "acceptance-user",
        "--scope", "用户批准验收候选毕业",
        "--actor-role", "compiler",
        "--json",
    ])
    assert promoted["promoted"] is True
    assert (TEST_VAULT / promoted["target"]).exists()
    assert "acceptance-capture-workflow.md" in (TEST_VAULT / "index.md").read_text(encoding="utf-8")
    assert "status: graduated" in (TEST_VAULT / candidate).read_text(encoding="utf-8")


def test_merge_workflow() -> None:
    proposed = run_km([
        "propose",
        "--title", "领星 API 鉴权增量边界",
        "--type", "query",
        "--tags", "api,auth,lingxing",
        "--source-ref", "conversation:acceptance-merge",
        "--suggested-action", "merge",
        "--suggested-target", "wiki/queries/lingxing-api-auth.md",
        "--value-reason", "补充正式页的验收边界",
        "--body", "验收补充：调用方应在刷新令牌后重放一次失败请求。",
        "--actor-role", "contributor",
        "--json",
    ])
    candidate = proposed["candidate_path"]
    run_km([
        "review", candidate,
        "--decision", "approve",
        "--reviewed-by", "acceptance-user",
        "--actor-role", "reviewer",
        "--json",
    ])
    merged = run_km([
        "merge", candidate,
        "--target", "wiki/queries/lingxing-api-auth.md",
        "--approved-by", "acceptance-user",
        "--scope", "用户批准合并验收边界",
        "--actor-role", "compiler",
        "--json",
    ])
    assert merged["merged"] is True
    target_body = (TEST_VAULT / merged["target"]).read_text(encoding="utf-8")
    assert "调用方应在刷新令牌后重放一次失败请求" in target_body
    assert "status: merged" in (TEST_VAULT / candidate).read_text(encoding="utf-8")


def test_duplicate_contributors() -> None:
    common = [
        "propose",
        "--title", "多 Agent 重复候选验收",
        "--type", "concept",
        "--tags", "ai-agent,workflow",
        "--suggested-target", "wiki/concepts/multi-agent-duplicate.md",
        "--value-reason", "验证多 Agent 去重并保留来源",
        "--body", "相同主题应合并贡献者和来源。",
        "--actor-role", "contributor",
        "--json",
    ]
    first = run_km([*common, "--source-ref", "conversation:agent-a", "--agent-id", "agent-a", "--source-session", "agent-a-session"])
    second = run_km([*common, "--source-ref", "conversation:agent-b", "--agent-id", "agent-b", "--source-session", "agent-b-session"])
    assert second["duplicate"] is True
    body = (TEST_VAULT / first["candidate_path"]).read_text(encoding="utf-8")
    assert "conversation:agent-a" in body and "conversation:agent-b" in body
    assert "agent-a" in body and "agent-b" in body


def test_dashboard_and_qmd() -> None:
    dashboard = run_km(["dashboard", "--actor-role", "reviewer", "--json"])
    assert (TEST_VAULT / dashboard["output"]).exists()
    qmd = run_km(["qmd-readiness", "--json"])
    assert qmd["ready"] is False
    assert qmd["top5_hit_rate"] >= 0.9


def test_http_adapter() -> None:
    mod = import_module(HTTP_ADAPTER, "km_http_acceptance")
    mod.ROLE = "compiler"
    mod.HTTP_TOKEN = "acceptance-token"
    server = ThreadingHTTPServer(("127.0.0.1", 0), mod.KMHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert http_get(port, "/health")["ok"] is True
        assert http_get(port, "/search?" + urllib.parse.urlencode({"q": "领星 API 鉴权", "limit": "1"}))["matches"]
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
    contributor = mcp_exchange(MCP_ADAPTER, "contributor", [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ])
    contributor_names = {item["name"] for item in contributor[1]["result"]["tools"]}
    assert "km_propose_capture" in contributor_names
    assert "km_promote_candidate" not in contributor_names
    assert "km_review_candidate" not in contributor_names

    compiler = mcp_exchange(MCP_ADAPTER, "compiler", [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "km_search", "arguments": {"query": "领星 API 鉴权", "limit": 1}}},
    ])
    compiler_names = {item["name"] for item in compiler[1]["result"]["tools"]}
    assert {"km_review_candidate", "km_promote_candidate", "km_merge_candidate"} <= compiler_names
    assert compiler[2]["result"]["structuredContent"]["matches"][0]["layer"] == "wiki"


def test_self_contained_plugin() -> None:
    plugin_cli = PLUGIN / "tools" / "km-cli" / "km.py"
    plugin_mcp = PLUGIN / "adapters" / "mcp" / "km_mcp.py"
    assert plugin_cli.exists() and plugin_mcp.exists()
    assert (PLUGIN / "skills" / "agentskm-capture" / "SKILL.md").exists()
    responses = mcp_exchange(plugin_mcp, "compiler", [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ])
    names = {item["name"] for item in responses[1]["result"]["tools"]}
    assert "km_configure_vault" in names and "km_promote_candidate" in names


def test_second_agent_config() -> None:
    output = TEST_ROOT / "claude.mcp.json"
    proc = run_process([
        sys.executable,
        str(MCP_CONFIG_RENDERER),
        "--agent", "claude",
        "--vault", str(TEST_VAULT),
        "--role", "contributor",
        "--output", str(output),
    ])
    assert proc.returncode == 0, proc.stderr
    server = json.loads(output.read_text(encoding="utf-8"))["mcpServers"]["agentskm"]
    assert server["args"][-1] == "contributor"
    env = os.environ.copy()
    env.update(server["env"])
    messages = "\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
        "",
    ])
    child = subprocess.run(
        [server["command"], *server["args"]],
        cwd=ROOT,
        input=messages,
        text=True,
        encoding="utf-8",
        env=env,
        capture_output=True,
    )
    assert child.returncode == 0, child.stderr
    responses = [json.loads(line) for line in child.stdout.splitlines() if line.strip()]
    names = {item["name"] for item in responses[1]["result"]["tools"]}
    assert "km_propose_capture" in names and "km_promote_candidate" not in names


def test_env() -> dict[str, str]:
    return {
        "AGENTSKM_DATA_ROOT": str(TEST_VAULT),
        "AGENTSKM_CONFIG": str(TEST_CONFIG),
        "PYTHONUTF8": "1",
    }


def run_km(args: list[str]) -> dict:
    proc = run_process([sys.executable, str(KM), *args])
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


def mcp_exchange(path: Path, role: str, messages: list[dict]) -> list[dict]:
    input_text = "\n".join(json.dumps(item, ensure_ascii=True) for item in messages) + "\n"
    proc = run_process([sys.executable, str(path), "--role", role], input_text=input_text)
    assert proc.returncode == 0, proc.stderr
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def http_get(port: int, route: str) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{route}", timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


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
