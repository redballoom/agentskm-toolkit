# AgentsKM Toolkit Bundle

This directory packages the thin, reusable entry points for AgentsKM.

It intentionally avoids duplicating core rules. The bundle points back to the
canonical repository locations:

- `tools/km-cli/km.py`
- `adapters/http/km_http.py`
- `adapters/mcp/km_mcp.py`
- `docs/review-dashboard.md`
- `docs/qmd-readiness.md`
- `docs/operations-runbook.md`

Use this directory as the portable reference set when copying or packaging the
tooling layer onto another machine.

The actual Codex plugin root used for installation is `bundles/plugins/agentskm-toolkit`.
