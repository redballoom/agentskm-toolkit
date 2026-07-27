# AgentsKM Toolkit Plugin

Installable Codex plugin root for `agentskm-toolkit`.

This folder is the source path referenced by `bundles/marketplace.json` and
`.agents/plugins/marketplace.json`.

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
