# AgentsKM Productization Plan

Status: active on `feat/uvx-productization`.

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

## Phase 1 Scope

- Add `pyproject.toml`.
- Add `src/agentskm_toolkit` package entrypoints.
- Provide `agentskm` console script.
- Support `agentskm mcp` and `uvx --from agentskm-toolkit agentskm mcp`
  startup shapes.
- Keep source-tree CLI/MCP paths working for development.
- Keep plugin runtime copies synchronized during transition.
- Add acceptance coverage for package and uvx entrypoints.

## Non-goals

- No PyPI production release yet.
- No npm wrapper yet.
- No plugin default switch to PyPI before the package is published.
- No Vault or user config in package artifacts.
- No rewrite of the KM workflow internals in this phase.

## Required Invariants

```text
contributor: search / propose / respond
reviewer:    + review / dashboard
compiler:    + promote / merge
```

These must remain true for source, installed package, and uvx startup modes.
