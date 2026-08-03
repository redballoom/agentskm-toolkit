# AgentsKM Toolkit Plugin

Codex plugin for a local AgentsKM Vault.

The plugin provides:

- the `agentskm-capture` Skill;
- a Codex MCP configuration backed by the published Python package;
- compatibility prompt shortcuts for common knowledge-base operations;
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

Ask Codex to run AgentsKM doctor to diagnose the active version, Profile, role,
config, and Vault. A code update requires an MCP reconnect or a new
conversation; the active process is never killed in place.

## Entry Points

The stable interaction surface is the `agentskm-capture` Skill and the
`agentskm` MCP server. Ask in natural language:

```text
Run AgentsKM doctor.
Check this conversation for reusable knowledge.
Search AgentsKM for <topic>.
```

`commands/*.md` remains as a compatibility layer for hosts that ingest plugin
command prompts. Current Codex builds may migrate these files into internal
Skills rather than display them in the slash-command menu. Therefore
`/km-doctor`, `/km-capture`, and `/km-search` are convenient text shortcuts,
not a guaranteed UI feature.

All entry points are intentionally conservative. Review and promotion remain
role-aware MCP operations: reviewer Profiles can approve candidates, and
compiler Profiles can promote or merge approved candidates.

## Expected Plugin Behavior

After the plugin is installed, Codex should expose the `agentskm` MCP tools and
load the `agentskm-capture` Skill. On first use, the MCP server creates a
default local config and empty Vault when no configuration exists. If MCP tools
are missing, use the plugin status view, reconnect the MCP server, or start a
new conversation. Do not look for a bundled `km.py` or manually edit the
plugin cache.
