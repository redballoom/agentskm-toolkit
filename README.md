# AgentsKM Toolkit

Reusable local toolchain for conversation-driven knowledge capture across
multiple Agent hosts. Live knowledge data stays in a user-controlled Vault and
is never bundled in the toolkit package or Codex plugin.

The product boundary is:

```text
Python package provides CLI/MCP capabilities
Codex plugin provides host experience and Skill behavior
%USERPROFILE%\.agentskm\config.json connects Profiles to the user Vault
Vault stores the user's knowledge assets
```

## Components

- `src/agentskm_toolkit`: productized Python package entrypoints
- `tools/km-cli`: deterministic capture, review, promotion, merge, locking,
  transactions, and audit log source implementation
- `adapters/mcp`: role-aware stdio MCP server source implementation
- `plugins/agentskm-toolkit`: Codex plugin, capture Skill, and MCP template
- `integrations`: host-specific notes for Claude, Cursor, Hermes, and others
- `scripts`: plugin packaging and MCP configuration generation
- `tests`: temporary-Vault end-to-end acceptance coverage

## Package Entry

For local development:

```powershell
pip install -e .
agentskm --version
agentskm doctor --profile codex
agentskm mcp --profile hermes-agent --host hermes
```

For install-on-use hosts after publishing:

```powershell
uvx --from agentskm-toolkit agentskm mcp --profile hermes-agent --host hermes
```

The first MCP start creates `%USERPROFILE%\.agentskm\config.json`, the selected
Profile, and the default empty Vault at `%USERPROFILE%\Documents\AgentsKM\vault`
when no configuration exists. Custom Vault paths remain controlled by the user
config file.

## Codex Plugin

The repository is also a Codex Git marketplace source through
`.agents/plugins/marketplace.json`. The plugin supplies the `agentskm-capture`
Skill and an MCP configuration template. Before the Python package is published,
the plugin template remains self-contained and starts its bundled MCP source.
After publishing, productized MCP startup should use:

```json
{
  "command": "uvx",
  "args": ["--from", "agentskm-toolkit", "agentskm", "mcp", "--profile", "codex", "--host", "codex"]
}
```

During development, the plugin still carries synchronized CLI/MCP runtime copies
so existing local plugin installs remain self-contained. Use
`scripts/build_plugin.py --check` to verify those copies are current.

## Other Agents

Generate a role-limited MCP configuration:

```powershell
python scripts/render_mcp_config.py `
  --agent hermes `
  --profile hermes-agent `
  --role contributor `
  --output hermes.mcp.json
```

Use `--runtime source` only for local source-tree testing. Published/user-facing
configs should use the default `uvx` runtime or `--runtime agentskm` after a
local package install.

## Roles

The role boundary is invariant across startup modes:

```text
contributor: search / propose / respond
reviewer:    + review / dashboard
compiler:    + promote / merge
```

A contributor can record user intent with `respond`, but cannot approve, promote,
merge, or write formal Wiki pages.

## Update Semantics

Source checkout and Git marketplace installs may use `agentskm update` to check
or refresh local code. In uvx/PyPI-style execution, update should be treated as a
version check plus reconnect instruction; the running package should not mutate
itself in place.
