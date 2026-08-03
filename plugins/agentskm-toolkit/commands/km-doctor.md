---
description: Diagnose AgentsKM config, Profile, role, and Vault
---

Use the AgentsKM MCP server from this plugin.

1. List the available AgentsKM MCP tools.
2. Confirm `km_doctor` is available.
3. Call `km_doctor`.
4. Report toolkit version, repository, config path, Profile, role, Vault path,
   state, failed checks, and next action.

Do not use a local source checkout or a bare `agentskm` CLI command. If
`km_doctor` is not available, report that as a plugin/MCP loading problem and
use `km_setup_status` only as a fallback diagnostic.
