# AgentsKM Productization Plan

Status: Python package released; lightweight Codex plugin migration in progress.

## Decision

AgentsKM Toolkit productization starts with the Python package and uvx path.
The Codex plugin remains the host-experience layer. Vault data remains outside
all release artifacts and is selected only through `%USERPROFILE%\.agentskm\config.json`.

```text
Python package -> CLI and MCP runtime
Codex plugin   -> Skill and MCP template
MCP server     -> cross-agent capability surface
config.json    -> Profile and Vault binding
Vault          -> user knowledge assets
```

## Completed Package Scope

- Add `pyproject.toml`.
- Add `src/agentskm_toolkit` package entrypoints.
- Provide `agentskm` console script.
- Support `agentskm mcp` and `uvx --from agentskm-toolkit agentskm mcp`
  startup shapes.
- Keep source-tree CLI/MCP paths working for development.
- Keep plugin runtime copies synchronized during the pre-release transition.
- Add acceptance coverage for package and uvx entrypoints.

## Lightweight Plugin Scope

- Keep Skill and MCP registration in the Codex plugin.
- Resolve the published CLI/MCP runtime through `uvx` with an exact version pin.
- Remove duplicated `tools/` and `adapters/` source from the plugin bundle.
- Keep Vault data and user config outside every release artifact.
- Validate Setup and role behavior through the same packaged runtime used by hosts.

## Required Invariants

```text
contributor: search / propose / respond
reviewer:    + review / dashboard
compiler:    + promote / merge
```

These must remain true for source, installed package, and uvx startup modes.
