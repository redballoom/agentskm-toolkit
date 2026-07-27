# Hermes Agent Integration

Install the AgentsKM plugin or MCP package in Hermes. Register the MCP server
with the stable Profile name `hermes-agent`:

```text
python <installed-package>/adapters/mcp/km_mcp.py --profile hermes-agent --host hermes
```

On the first start, an unconfigured installation automatically creates:

```text
profile: hermes-agent
role: contributor
config: %USERPROFILE%\.agentskm\config.json
vault: %USERPROFILE%\Documents\AgentsKM\vault
```

For an existing shared Vault, change `vaults.main.path` in the config. Hermes
re-reads the Profile and Vault on each operation. No environment variable or
restart is required for that path change.

Manual Setup remains available for recovery:

```powershell
python <installed-package>\tools\km-cli\km.py setup `
  --profile hermes-agent `
  --host hermes `
  --actor-id hermes-agent `
  --role contributor `
  --vault-name main
```

The server exposes search, reminder, validation, diagnostics, update, and
candidate proposal tools. It does not expose review, promote, merge, or
configuration-write tools.

Setup is idempotent. If `hermes-agent` already exists with different settings,
the CLI reports the conflict and does not overwrite it.
