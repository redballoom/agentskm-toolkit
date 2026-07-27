# AgentsKM MCP Adapter

Self-contained stdio adapter over `tools/km-cli/km.py --json`.

```powershell
python adapters/mcp/km_mcp.py --profile hermes-agent --host hermes
python adapters/mcp/km_mcp.py --profile codex --host codex --bootstrap-role compiler
```

The adapter resolves Vault and role from the selected Agent Profile.
Contributor profiles expose read, reminder, and propose tools.
Reviewer profiles additionally expose review and dashboard tools. Compiler
profiles additionally expose promote and merge tools.

When configuration or the requested Profile is missing, the server invokes the
bundled CLI once to create the Profile and default empty Vault. Legacy, invalid,
or conflicting state remains untouched and exposes Setup, Doctor, and Update
tools for recovery. Configuration is re-read for each operation.

`km_update` uses the host's supported update driver. Updated executable code
requires an MCP reconnect or a new conversation; ordinary Setup and Vault path
changes do not.

Use `scripts/render_mcp_config.py` to generate Claude Code, Cursor, or generic
MCP configuration files with an explicit Profile.
