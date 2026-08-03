# AgentsKM Toolkit Plugin

Codex plugin for a local AgentsKM Vault.

The plugin provides:

- the `agentskm-capture` Skill;
- a Codex MCP configuration backed by the published Python package;
- slash command prompts for common knowledge-base operations;
- local usage guidance for setup, capture, review, and promotion workflows.

The plugin is intentionally lightweight. CLI and MCP implementation code is
not copied into the plugin; `uvx` resolves the pinned PyPI runtime on demand:

```powershell
uvx --from agentskm-toolkit==0.4.4 agentskm mcp --profile codex --host codex --bootstrap-role compiler
```

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

`uvx` must be available on the host. The package version is pinned in
`.mcp.json` so a plugin release remains reproducible; upgrading AgentsKM means
updating the plugin runtime pin and reinstalling the plugin.

Run `agentskm doctor --profile codex` or `km_doctor` to diagnose the active
version, Profile, role, config, and Vault. A code update requires an MCP
reconnect or a new conversation; the active process is never killed in place.

## Slash Commands

The plugin includes prompt-backed slash commands in `commands/*.md`. These
commands guide Codex to use the plugin MCP tools; they do not bypass role checks
or require a separate bundled command runtime.

```text
/km-doctor   Check package version, Profile, role, config, and Vault health.
/km-capture  Review the current conversation and propose one reusable Inbox candidate.
/km-search   Search reviewed Wiki knowledge first, then clearly label Inbox hits.
```

Use `/km-doctor` when setup, path selection, `uvx`, or MCP startup is unclear.
Use `/km-capture` when the user explicitly asks to preserve a result from the
current conversation. Use `/km-search <topic>` before repeating investigation
work that may already exist in the Vault.

These slash commands are intentionally conservative. Review and promotion remain
role-aware MCP operations: reviewer Profiles can approve candidates, and compiler
Profiles can promote or merge approved candidates.
