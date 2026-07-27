# AgentsKM MCP Adapter

Self-contained stdio adapter over `tools/km-cli/km.py --json`.

```powershell
python adapters/mcp/km_mcp.py --role contributor
python adapters/mcp/km_mcp.py --role compiler
```

Contributor profiles expose read, configure, reminder, and propose tools.
Reviewer profiles additionally expose review and dashboard tools. Compiler
profiles additionally expose promote and merge tools.

The adapter inherits `AGENTSKM_DATA_ROOT`, or uses the persistent binding in
`%USERPROFILE%\.agentskm\config.json`. It never edits Markdown directly.

Use `scripts/render_mcp_config.py` to generate Claude Code, Cursor, or generic
MCP configuration files with an explicit vault and role.
