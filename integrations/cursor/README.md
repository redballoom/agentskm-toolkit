# Cursor Integration

Generate a contributor MCP configuration:

```powershell
python scripts/render_mcp_config.py `
  --agent cursor `
  --vault D:\path\to\agentskm-vault `
  --role contributor `
  --output .cursor\mcp.json
```

Add a short project rule instructing Cursor to search Wiki first, submit only
verified reusable outcomes, and leave promotion to a compiler profile.
