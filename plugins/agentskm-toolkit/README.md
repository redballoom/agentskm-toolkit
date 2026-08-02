# AgentsKM Toolkit Plugin

Codex plugin for a local AgentsKM Vault.

The plugin provides:

- the `agentskm-capture` Skill;
- a self-contained MCP template for local Git marketplace installs;
- local usage guidance for setup, capture, review, and promotion workflows.

Live knowledge is never bundled in the plugin. Profiles and Vault paths are
stored in `%USERPROFILE%\.agentskm\config.json`. The default Vault is:

```text
%USERPROFILE%\Documents\AgentsKM\vault
```

On first MCP start, AgentsKM creates the selected Profile, user config, and a
minimal empty Vault when they do not exist. For Codex, the default Profile is:

```text
profile: codex
role: compiler
```

Development note: this plugin currently still carries synchronized CLI/MCP
runtime copies so local Git marketplace installs remain self-contained. After
the Python package is published, the productized path is:

```powershell
uvx --from agentskm-toolkit agentskm mcp --profile codex --host codex --bootstrap-role compiler
```

Run `agentskm doctor --profile codex` or `km_doctor` to diagnose the active
version, Profile, role, config, and Vault. A code update requires an MCP
reconnect or a new conversation; the active process is never killed in place.
