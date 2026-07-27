# AgentsKM Toolkit Plugin

Self-contained plugin for a local AgentsKM vault.

The package includes the knowledge-capture Skill, KM CLI, and stdio MCP
adapter. On the first MCP start, it creates the `codex` Profile, user config,
and a minimal empty Vault automatically when they do not exist:

```text
config: %USERPROFILE%\.agentskm\config.json
vault:  %USERPROFILE%\Documents\AgentsKM\vault
profile: codex (compiler)
```

Profiles and Vault paths are stored in
`%USERPROFILE%\.agentskm\config.json`. The installed plugin does not require a
Toolkit source checkout. Change the `main` Vault path in the config to bind all
Profiles to an existing Vault. Live knowledge is never bundled in the plugin.

Run `km doctor` to diagnose the active version, Profile, role, config, and
Vault. Run `km update` to refresh a Git marketplace installation from GitHub.
Configuration changes are read dynamically. A code update requires an MCP
reconnect or a new conversation; the active process is never killed in place.

The plugin, MCP adapter, and HTTP adapter are thin wrappers. The KM CLI remains
the only place that performs writes, locking, validation, promotion, and audit
logging.
