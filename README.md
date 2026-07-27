# AGENTSKM

This repository is the split-out code and plugin side of AgentsKM.
It is meant to be uploaded to GitHub and reused by other agents without
shipping the live knowledge data itself.

Included here:

- `tools/km-cli` for the deterministic knowledge-base core
- `adapters/mcp` and `adapters/http` for thin integrations
- `plugins/agentskm-toolkit` for Codex plugin packaging
- `docs/` for the protocol, runbook, and architecture notes
- `bundles/` for marketplace wiring
- `tests/` for validation coverage

Not included here:

- `000_Inbox/`
- `raw/`
- `wiki/`
- `index.md`
- `log.md`

The intended deployment model is: keep this repository as the toolchain,
and bind it to a separate local knowledge repository at runtime.
