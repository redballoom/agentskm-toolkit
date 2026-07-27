#!/usr/bin/env python3
"""Acceptance smoke tests for AgentsKM.

The tests use dry-run paths for write commands. They should not create or
promote knowledge pages.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
KM = ROOT / "tools" / "km-cli" / "km.py"
HTTP_ADAPTER = ROOT / "adapters" / "http" / "km_http.py"
MCP_ADAPTER = ROOT / "adapters" / "mcp" / "km_mcp.py"


def main() -> int:
    test_cli_status()
    test_cli_search_prioritizes_wiki()
    test_cli_pending_guardrail()
    test_cli_propose_dry_run()
    test_cli_promote_guardrail()
    test_qmd_readiness_report()
    test_http_adapter()
    test_mcp_adapter()
    print("Acceptance workflow passed.")
    return 0


def test_cli_status() -> None:
    payload = run_km(["status", "--json"])
    assert payload["ok"] is True
    assert payload["layers"]["wiki"] >= 1
    assert payload["layers"]["inbox"] >= 1


def test_cli_search_prioritizes_wiki() -> None:
    payload = run_km(["search", "领星 API 鉴权", "--limit", "1", "--json"])
    assert payload["ok"] is True
    assert payload["count"] == 1
    assert payload["matches"][0]["layer"] == "wiki"
    assert payload["matches"][0]["path"] == "wiki/queries/lingxing-api-auth.md"


def test_cli_pending_guardrail() -> None:
    payload = run_km(["pending", "--json"])
    assert payload["ok"] is True
    assert any(item["status"] == "pending-source-review" for item in payload["candidates"])


def test_cli_propose_dry_run() -> None:
    payload = run_km([
        "propose",
        "--title", "验收测试候选",
        "--type", "concept",
        "--tags", "methodology",
        "--source-ref", "raw/articles/lingxing-api-access-token-doc.md",
        "--suggested-target", "wiki/concepts/acceptance-test.md",
        "--value-reason", "验证 propose dry-run",
        "--body", "这是一条 dry-run 验收候选。",
        "--dry-run",
        "--json",
    ])
    assert payload["ok"] is True
    assert payload["dry_run"] is True
    candidate_path = ROOT / payload["candidate_path"]
    assert not candidate_path.exists()


def test_cli_promote_guardrail() -> None:
    proc = run_process([
        sys.executable,
        str(KM),
        "promote",
        "000_Inbox/ai-agent-platform-comparison-2025.md",
        "--target",
        "wiki/comparisons/ai-agent-platform-comparison-2025.md",
        "--dry-run",
        "--json",
    ])
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert "source_refs" in payload["error"]


def test_qmd_readiness_report() -> None:
    payload = run_km(["qmd-readiness", "--json"])
    assert payload["ok"] is True
    assert payload["ready"] is False
    assert payload["top5_hit_rate"] >= 0.9
    output = ROOT / payload["output"]
    assert output.exists()
    body = output.read_text(encoding="utf-8")
    assert "QMD Readiness" in body
    assert "Recommendation" in body


def test_http_adapter() -> None:
    mod = import_module(HTTP_ADAPTER, "km_http_acceptance")
    server = ThreadingHTTPServer(("127.0.0.1", 0), mod.KMHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        health = http_get(port, "/health")
        assert health["ok"] is True
        search = http_get(port, "/search?" + urllib.parse.urlencode({"q": "领星 API 鉴权", "limit": "1"}))
        assert search["matches"][0]["layer"] == "wiki"
        guardrail_status, guardrail = http_post(port, "/promote", {
            "candidate": "000_Inbox/ai-agent-platform-comparison-2025.md",
            "target": "wiki/comparisons/ai-agent-platform-comparison-2025.md",
            "dry_run": True,
        })
        assert guardrail_status == 400
        assert guardrail["ok"] is False
    finally:
        server.shutdown()
        server.server_close()


def test_mcp_adapter() -> None:
    messages = "\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "acceptance", "version": "0"}}}, ensure_ascii=True),
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, ensure_ascii=True),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, ensure_ascii=True),
        json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "km_search", "arguments": {"query": "领星 API 鉴权", "limit": 1}}}, ensure_ascii=True),
        json.dumps({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "km_promote_candidate", "arguments": {"candidate": "000_Inbox/ai-agent-platform-comparison-2025.md", "target": "wiki/comparisons/ai-agent-platform-comparison-2025.md", "dry_run": True}}}, ensure_ascii=True),
        "",
    ])
    proc = run_process([sys.executable, str(MCP_ADAPTER)], input_text=messages)
    assert proc.returncode == 0
    responses = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    assert responses[0]["result"]["serverInfo"]["name"] == "agentskm"
    assert len(responses[1]["result"]["tools"]) >= 8
    search_result = responses[2]["result"]["structuredContent"]
    assert search_result["matches"][0]["layer"] == "wiki"
    guardrail = responses[3]["result"]
    assert guardrail["isError"] is True


def run_km(args: list[str]) -> dict:
    proc = run_process([sys.executable, str(KM), *args])
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def run_process(args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        input=input_text,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def http_get(port: int, route: str) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{route}", timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post(port: int, route: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{route}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
