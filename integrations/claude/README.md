# Claude Code Integration

Generate a contributor MCP configuration:

```powershell
python scripts/render_mcp_config.py `
  --agent claude `
  --vault D:\path\to\agentskm-vault `
  --role contributor `
  --output .mcp.json
```

Copy or reference `CLAUDE.md` from the project instructions that should use
AgentsKM. Grant `compiler` only to a trusted host that must apply approved
Wiki changes.
