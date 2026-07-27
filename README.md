# AgentsKM Toolkit

Reusable local toolchain for conversation-driven knowledge capture across
multiple Agent hosts. Live knowledge data stays in a separate private
`agentskm-vault` repository.

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

Clone the toolkit and private Vault, then bind them once:

```powershell
python tools/km-cli/km.py configure --vault D:\path\to\agentskm-vault
python tools/km-cli/km.py status
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
  --vault D:\path\to\agentskm-vault `
  --role contributor `
  --output .mcp.json
```

Use `compiler` only for a trusted Agent that must apply explicit user
approvals. A contributor can search and propose but cannot approve or write
formal Wiki pages.
