# AgentsKM MCP Adapter

Self-contained stdio adapter over `tools/km-cli/km.py --json`.

```powershell
python adapters/mcp/km_mcp.py --profile hermes-agent
python adapters/mcp/km_mcp.py --profile codex
```

The adapter resolves Vault and role from the selected Agent Profile.
Contributor profiles expose read, reminder, and propose tools.
Reviewer profiles additionally expose review and dashboard tools. Compiler
profiles additionally expose promote and merge tools.

When configuration or the requested Profile is missing, the server enters
read-only Bootstrap mode and exposes only `km_setup_status` and
`km_setup_instructions`. Setup writes are performed by the local CLI after
user confirmation, never by MCP. Restart the MCP server after Setup.

Use `scripts/render_mcp_config.py` to generate Claude Code, Cursor, or generic
MCP configuration files with an explicit Profile.
