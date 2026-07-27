# Hermes Agent Integration

Install the AgentsKM plugin or MCP package in Hermes. Register the MCP server
with the stable Profile name `hermes-agent`:

```text
python <installed-package>/adapters/mcp/km_mcp.py --profile hermes-agent
```

On the first start, an unconfigured installation exposes only:

```text
km_setup_status
km_setup_instructions
```

Ask Hermes to check AgentsKM Setup. After it reports the config path and
available Vault information, confirm this default assignment:

```text
profile: hermes-agent
host: hermes
role: contributor
vault: main
```

Hermes may then run the bundled CLI command reported by
`km_setup_instructions`, adding the Vault path when this is the first local
configuration:

```powershell
python <installed-package>\tools\km-cli\km.py setup `
  --profile hermes-agent `
  --host hermes `
  --actor-id hermes-agent `
  --role contributor `
  --vault-name main `
  --vault D:\path\to\agentskm-vault
```

Restart Hermes or reconnect the MCP server after Setup. The restarted server
then exposes search, reminder, validation, and candidate proposal tools for the
shared Vault. It does not expose review, promote, merge, or configuration-write
tools.

Setup is idempotent. If `hermes-agent` already exists with different settings,
the CLI reports the conflict and does not overwrite it.
