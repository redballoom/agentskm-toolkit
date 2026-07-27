# AgentsKM Toolkit

Reusable local toolchain for conversation-driven knowledge capture across
multiple Agent hosts. Live knowledge data stays in a separate private
`agentskm-vault` repository.

The publishable source of truth is this standalone `agentskm-toolkit` Git
repository. Separate Vault workspaces are used only for integration tests and
experiments; they are not plugin release sources. See
`docs/toolkit-development-workflow.md`.

## Components

- `tools/km-cli`: deterministic capture, review, promotion, merge, locking,
  transactions, and audit log
- `adapters/mcp`: role-aware stdio MCP server
- `adapters/http`: optional authenticated localhost adapter
- `plugins/agentskm-toolkit`: self-contained Codex plugin and capture Skill
- `integrations`: thin Claude Code and Cursor entry points
- `scripts`: plugin packaging and MCP configuration generation
- `tests`: temporary-Vault end-to-end acceptance coverage

## Local Setup

For source development, clone the toolkit. End users install the plugin/package
and run Setup against an existing local Vault:

```powershell
python tools/km-cli/km.py setup `
  --profile codex --host codex --role compiler `
  --vault-name main --vault D:\path\to\agentskm-vault `
  --confirm-compiler
```

## Codex Plugin

The repository is a Codex marketplace source through
`.agents/plugins/marketplace.json`. The installed plugin includes its own CLI,
MCP adapter, and `agentskm-capture` Skill; it does not depend on paths outside
the installed plugin cache.

## Other Agents

Generate a role-limited MCP configuration:

```powershell
python scripts/render_mcp_config.py `
  --agent claude `
  --profile claude `
  --output .mcp.json
```

Use `compiler` only for a trusted Agent that must apply explicit user
approvals. A contributor can search and propose but cannot approve or write
formal Wiki pages.
