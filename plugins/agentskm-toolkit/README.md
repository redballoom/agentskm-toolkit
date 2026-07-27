# AgentsKM Toolkit Plugin

Self-contained Codex plugin for a separately cloned AgentsKM vault.

The package includes the knowledge-capture Skill, KM CLI, and stdio MCP
adapter. Bind a vault once with the `km_configure_vault` MCP tool or:

```powershell
python tools/km-cli/km.py configure --vault D:\path\to\agentskm-vault
```

The binding is stored in `%USERPROFILE%\.agentskm\config.json`. The plugin
never bundles or uploads live knowledge data.

This plugin expects the reusable toolkit repository and the knowledge vault to
be split:

```text
AGENTSKM/
├── agentskm-toolkit/
└── agentskm-vault/
```

Set `AGENTSKM_DATA_ROOT` to the local vault path before using the CLI, MCP
server, or HTTP adapter:

```powershell
$env:AGENTSKM_DATA_ROOT="D:\Human-Agent_Collab\AGENTSKM\agentskm-vault"
```

The plugin, MCP adapter, and HTTP adapter are thin wrappers. The KM CLI remains
the only place that performs writes, locking, validation, promotion, and audit
logging.
