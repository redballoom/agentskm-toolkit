# AgentsKM Toolkit Plugin

Self-contained plugin for a local AgentsKM vault.

The package includes the knowledge-capture Skill, KM CLI, and stdio MCP
adapter. On first use, the MCP server checks the `codex` Profile. If it is
missing, only read-only Setup tools are exposed. After user confirmation, run
the bundled CLI shown by `km_setup_instructions`, for example:

```powershell
python tools/km-cli/km.py setup `
  --profile codex `
  --host codex `
  --role compiler `
  --vault-name main `
  --vault D:\path\to\agentskm-vault `
  --confirm-compiler
```

Profiles and Vault paths are stored in
`%USERPROFILE%\.agentskm\config.json`. The installed plugin does not require a
Toolkit source checkout. An existing Vault may be cloned, restored, or already
present locally; live knowledge is never bundled in the plugin.

The plugin, MCP adapter, and HTTP adapter are thin wrappers. The KM CLI remains
the only place that performs writes, locking, validation, promotion, and audit
logging.
