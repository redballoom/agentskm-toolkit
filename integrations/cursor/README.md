# Cursor Integration

Add a contributor server to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "agentskm": {
      "command": "uvx",
      "args": [
        "--from", "agentskm-toolkit==0.5.0",
        "agentskm", "mcp",
        "--profile", "cursor",
        "--host", "cursor",
        "--bootstrap-role", "contributor"
      ]
    }
  }
}
```

`uvx` must be available on `PATH`; no Toolkit clone or global CLI install is
required. Add a project rule telling Cursor to search reviewed Wiki knowledge,
submit only verified reusable outcomes, and leave approval/promotion to the
appropriate reviewer/compiler Profile.
