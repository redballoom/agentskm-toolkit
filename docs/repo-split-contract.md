# Repo Split Contract

This repository is the reusable toolchain layer.
The knowledge repository is kept separately and mounted locally when the CLI,
MCP adapter, or plugin runs.

Recommended layout:

- `AGENTSKM/` -> code, plugin, adapters, docs, tests
- `agentskm-vault/` -> `000_Inbox/`, `raw/`, `wiki/`, `index.md`, `log.md`

The split boundary is deliberate:

- code repo is safe to publish
- data repo can stay private
- agents can reinstall the plugin without moving knowledge history
