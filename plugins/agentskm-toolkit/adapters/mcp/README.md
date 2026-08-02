# AgentsKM MCP Adapter

Role-aware stdio MCP server for AgentsKM.

Productized startup:

```powershell
agentskm mcp --profile hermes-agent --host hermes
uvx --from agentskm-toolkit agentskm mcp --profile hermes-agent --host hermes
uvx --from agentskm-toolkit agentskm mcp --profile codex --host codex --bootstrap-role compiler
```

Source-tree development startup remains available:

```powershell
python adapters/mcp/km_mcp.py --profile hermes-agent --host hermes
python adapters/mcp/km_mcp.py --profile codex --host codex --bootstrap-role compiler
```

The adapter resolves Vault and role from the selected Agent Profile.
Contributor profiles expose read, reminder, propose, and contributor-safe
response tools. Reviewer profiles additionally expose review and dashboard tools.
Compiler profiles additionally expose promote and merge tools.

When configuration or the requested Profile is missing, the server invokes the
bundled CLI once to create the Profile and default empty Vault. Legacy, invalid,
or conflicting state remains untouched and exposes Setup, Doctor, and Update
tools for recovery. Configuration is re-read for each operation.

Use `scripts/render_mcp_config.py` to generate Claude, Cursor, Hermes, Codex, or
generic MCP configuration files. The default rendered runtime is `uvx`; use
`--runtime source` for local acceptance tests.
