#!/usr/bin/env python3
"""Local HTTP adapter for AgentsKM.

This adapter is intentionally thin: every operation shells out to the KM CLI
with --json and returns the parsed result. It must not duplicate KM rules.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[2]
KM = ROOT / "tools" / "km-cli" / "km.py"
MAX_BODY = 1024 * 1024
PROFILE = "default"
CONFIG_PATH = ""
HTTP_TOKEN = ""


class KMHandler(BaseHTTPRequestHandler):
    server_version = "AgentsKMHTTP/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == "/health":
                self.write_json(200, {"ok": True, "service": "agentskm-http"})
                return
            if parsed.path == "/status":
                self.run_cli(["status", "--json"])
                return
            if parsed.path == "/pending":
                self.run_cli(["pending", "--json"])
                return
            if parsed.path == "/reminders":
                self.run_cli(["reminders", "--json"])
                return
            if parsed.path == "/validate":
                self.run_cli(["validate", "--json"])
                return
            if parsed.path == "/lint":
                self.run_cli(["lint", "--json"])
                return
            if parsed.path == "/search":
                search_query = one(query, "q")
                if not search_query:
                    self.write_json(400, {"ok": False, "error": "Missing query parameter: q"})
                    return
                limit = one(query, "limit") or "10"
                self.run_cli(["search", search_query, "--limit", limit, "--json"])
                return
            self.write_json(404, {"ok": False, "error": f"Unknown endpoint: {parsed.path}"})
        except ValueError as exc:
            self.write_json(400, {"ok": False, "error": str(exc)})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if not self.authorized():
                self.write_json(401, {"ok": False, "error": "Missing or invalid bearer token"})
                return
            body = self.read_body()
            if parsed.path == "/propose":
                self.run_cli(build_propose_args(body))
                return
            if parsed.path == "/review":
                self.run_cli(build_review_args(body))
                return
            if parsed.path == "/promote":
                self.run_cli(build_promote_args(body))
                return
            if parsed.path == "/merge":
                self.run_cli(build_merge_args(body))
                return
            self.write_json(404, {"ok": False, "error": f"Unknown endpoint: {parsed.path}"})
        except ValueError as exc:
            self.write_json(400, {"ok": False, "error": str(exc)})

    def read_body(self) -> dict[str, object]:
        length_raw = self.headers.get("Content-Length", "0")
        try:
            length = int(length_raw)
        except ValueError as exc:
            raise ValueError("Invalid Content-Length") from exc
        if length > MAX_BODY:
            raise ValueError("Request body is too large")
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON body: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def authorized(self) -> bool:
        supplied = self.headers.get("Authorization", "")
        expected = f"Bearer {HTTP_TOKEN}"
        return bool(HTTP_TOKEN) and secrets.compare_digest(supplied, expected)

    def run_cli(self, args: list[str]) -> None:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        args = [*args, "--profile", PROFILE]
        if CONFIG_PATH:
            args.extend(["--config", CONFIG_PATH])
        proc = subprocess.run(
            [sys.executable, str(KM), *args],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            env=env,
            capture_output=True,
        )
        payload = parse_cli_json(proc.stdout, proc.stderr)
        status = 200 if proc.returncode == 0 else 400
        self.write_json(status, payload)

    def write_json(self, status: int, payload: dict[str, object]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def one(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key, [])
    return values[0] if values else ""


def parse_cli_json(stdout: str, stderr: str) -> dict[str, object]:
    text = (stdout or "").strip()
    if text:
        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass
    return {
        "ok": False,
        "error": (stderr or stdout or "KM CLI returned no output").strip(),
    }


def build_propose_args(data: dict[str, object]) -> list[str]:
    title = require_string(data, "title")
    value_reason = require_string(data, "value_reason")
    args = [
        "propose",
        "--title", title,
        "--value-reason", value_reason,
        "--json",
    ]
    append_option(args, data, "type", "--type")
    append_option(args, data, "tags", "--tags")
    append_option(args, data, "agent_id", "--agent-id")
    append_option(args, data, "source_tool", "--source-tool")
    append_option(args, data, "source_session", "--source-session")
    append_option(args, data, "suggested_action", "--suggested-action")
    append_option(args, data, "suggested_target", "--suggested-target")
    append_option(args, data, "confidence", "--confidence")
    append_option(args, data, "sensitivity", "--sensitivity")
    append_option(args, data, "body", "--body")
    append_option(args, data, "body_file", "--body-file")
    append_option(args, data, "slug", "--slug")
    for source_ref in string_list(data.get("source_refs")):
        args.extend(["--source-ref", source_ref])
    if bool(data.get("dry_run", False)):
        args.append("--dry-run")
    return args


def build_promote_args(data: dict[str, object]) -> list[str]:
    candidate = require_string(data, "candidate")
    args = ["promote", candidate, "--json"]
    append_option(args, data, "target", "--target")
    append_option(args, data, "title", "--title")
    append_option(args, data, "summary", "--summary")
    args.extend(["--approved-by", require_string(data, "approved_by")])
    args.extend(["--scope", require_string(data, "scope")])
    if bool(data.get("dry_run", False)):
        args.append("--dry-run")
    return args


def build_review_args(data: dict[str, object]) -> list[str]:
    args = [
        "review",
        require_string(data, "candidate"),
        "--decision", require_string(data, "decision"),
        "--json",
    ]
    append_option(args, data, "reviewed_by", "--reviewed-by")
    append_option(args, data, "reason", "--reason")
    append_option(args, data, "until", "--until")
    if bool(data.get("dry_run", False)):
        args.append("--dry-run")
    return args


def build_merge_args(data: dict[str, object]) -> list[str]:
    args = [
        "merge",
        require_string(data, "candidate"),
        "--target", require_string(data, "target"),
        "--approved-by", require_string(data, "approved_by"),
        "--scope", require_string(data, "scope"),
        "--json",
    ]
    if bool(data.get("dry_run", False)):
        args.append("--dry-run")
    return args


def require_string(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing required string field: {key}")
    return value


def append_option(args: list[str], data: dict[str, object], key: str, flag: str) -> None:
    value = data.get(key)
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError(f"Field must be a string: {key}")
    if value:
        args.extend([flag, value])


def string_list(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("source_refs must be a list of strings")
    return [item for item in value if item]


def main(argv: list[str] | None = None) -> int:
    global PROFILE, CONFIG_PATH, HTTP_TOKEN
    parser = argparse.ArgumentParser(prog="km-http")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--profile", default="default")
    parser.add_argument("--config")
    parser.add_argument("--token", default=os.environ.get("AGENTSKM_HTTP_TOKEN", ""))
    args = parser.parse_args(argv)
    if not args.token:
        parser.error("--token or AGENTSKM_HTTP_TOKEN is required")
    PROFILE = args.profile
    CONFIG_PATH = str(Path(args.config).expanduser().resolve()) if args.config else ""
    HTTP_TOKEN = args.token

    server = ThreadingHTTPServer((args.host, args.port), KMHandler)
    print(f"AgentsKM HTTP adapter listening on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
