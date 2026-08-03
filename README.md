# AgentsKM Toolkit

AgentsKM is a local, conversation-driven knowledge workflow shared by multiple
Agent hosts. User knowledge remains in a configured Vault and is never bundled
in the Python package or Codex plugin.

```text
Codex Plugin -> Skill + MCP registration
MCP          -> structured Agent tools and role-aware visibility
CLI          -> the only configuration, permission, Vault, lock, transaction,
                audit, Inbox, search, review, and Wiki implementation
Vault        -> user-owned knowledge data
```

`src/agentskm_toolkit` is the only runtime source of truth. `tools/km-cli` and
`adapters/mcp` are compatibility launchers for old source-checkout workflows;
they contain no business logic.

## Codex Plugin

After the matching `0.5.0` runtime is published, install the official GitHub
Marketplace source and plugin:

```powershell
codex plugin marketplace add redballoom/agentskm-toolkit --ref <stable-ref> --sparse plugins/agentskm-toolkit
codex plugin add agentskm-toolkit@agentskm-official
```

The plugin installs one `agentskm` Skill and an MCP registration. On MCP start,
`uvx` resolves the exact PyPI runtime pin; no repository clone or global
`agentskm` installation is required. The host must provide `uvx` on `PATH`.

The first start creates the requested Profile, the config at
`%USERPROFILE%\.agentskm\config.json`, and an empty default Vault at
`%USERPROFILE%\Documents\AgentsKM\vault` when they do not exist.

`commands/*.md` is temporarily retained only for the 0.5.0 UI migration
experiment. Codex may convert those files into `source-command-*` Skills;
natural-language use of the formal `agentskm` Skill is the product contract.

## Other Agents

There is no universal cross-host plugin format. Hermes, Claude, Cursor, and
other MCP-capable hosts use the same runtime directly:

```text
command: uvx
args: --from agentskm-toolkit==0.5.0 agentskm mcp --profile <profile> --host <host> --bootstrap-role contributor
```

Use `scripts/render_mcp_config.py` only as a source-repository convenience for
generating this configuration. End users do not need the script or a clone.

## Roles

```text
contributor: search / propose / respond
reviewer:    + review / dashboard
compiler:    + promote / merge
```

Roles come from the selected Profile in the user config. MCP hides tools above
the session role, while CLI independently enforces every write. Role changes
require an MCP reconnect so the host receives a stable tool list.

## Development

```powershell
pip install -e .
agentskm --version
python scripts/check_repo_purity.py
python scripts/check_versions.py
python scripts/build_plugin.py --check
python tests/acceptance/test_km_workflow.py
```

Acceptance tests write only to temporary Vaults. The `0.5.0` plugin pin must not
be exposed through a stable Marketplace ref until production PyPI can install
`agentskm-toolkit==0.5.0`.
