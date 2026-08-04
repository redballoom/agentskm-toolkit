# Hermes Agent Integration

Register AgentsKM as a stdio MCP server in Hermes:

```json
{
  "command": "uvx",
  "args": [
    "--from", "agentskm-toolkit==0.5.1",
    "agentskm", "mcp",
    "--profile", "hermes-agent",
    "--host", "hermes",
    "--bootstrap-role", "contributor"
  ]
}
```

No Toolkit clone or global CLI install is required. `uvx` must be available on
`PATH`. First startup creates the contributor Profile, user config, and empty
default Vault when missing.

To share an existing Vault, set `vaults.main.path` in
`%USERPROFILE%\.agentskm\config.json`, then reconnect MCP. Setup is idempotent;
a conflicting existing Profile is reported and never overwritten.

Hermes exposes search, reminders, validation, diagnostics, update, proposal,
and contributor response tools. It cannot review, approve, promote, or merge.
