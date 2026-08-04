# Claude Code Integration

Add this contributor server to Claude Code's MCP configuration:

```json
{
  "mcpServers": {
    "agentskm": {
      "command": "uvx",
      "args": [
        "--from", "agentskm-toolkit==0.5.1",
        "agentskm", "mcp",
        "--profile", "claude",
        "--host", "claude",
        "--bootstrap-role", "contributor"
      ]
    }
  }
}
```

`uvx` must be available on `PATH`; no Toolkit clone is required. Add the short
workflow rules from `CLAUDE.md` to projects that should use AgentsKM. Grant a
compiler Profile only to a trusted host that must apply approved Wiki changes.
