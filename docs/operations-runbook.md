# AgentsKM Operations Runbook

## Install And Bootstrap

Codex installs the GitHub Marketplace plugin. Other Agent hosts register the
same pinned PyPI runtime as a stdio MCP server:

```powershell
uvx --from agentskm-toolkit==0.5.1 agentskm mcp `
  --profile hermes-agent --host hermes --bootstrap-role contributor
```

No user installation requires a Toolkit clone or a global CLI. `uvx` must be
on `PATH`. First MCP startup creates, when missing:

```text
config: %USERPROFILE%\.agentskm\config.json
Vault:  %USERPROFILE%\Documents\AgentsKM\vault
Codex:  codex / compiler
Other:  host-specific Profile / contributor
```

The config file is the only source for Vault paths and Profile roles. Do not
use environment variables. After Setup, a role change, or an update, reconnect
MCP so the host receives the correct fixed tool list.

Diagnose through MCP with `km_doctor`, or in a recovery terminal:

```powershell
uvx --from agentskm-toolkit==0.5.1 agentskm doctor --profile codex
```

## Daily Workflow

1. Search Wiki before repeating relevant prior investigation.
2. Treat Inbox matches as unreviewed.
3. Propose one verified reusable result with `km_propose_capture`.
4. Tell the user its title, value, action/target, then ask
   `沉淀 / 稍后 / 忽略`.
5. Record the response without deleting the Inbox audit record.

Inbox is shared by all Profiles connected to the Vault. Candidate provenance
must retain `agent_id`, `source_tool`, `source_session`, and `source_refs`.

## Approval

```text
contributor -> search, propose, respond
reviewer    -> approve/snooze/reject, dashboard
compiler    -> promote or merge an approved candidate
```

A contributor records `capture` intent but cannot approve. Promotion and merge
require candidate status `approved` plus explicit `approved_by` and `scope`
metadata tied to the user's decision.

## HTTP Adapter

The HTTP adapter is experimental, source-only, and not part of the PyPI product
surface. Bind it to loopback only and require a token for every write. Do not
advertise it as installed by the plugin or expose it publicly.

## Verification

From a source checkout:

```powershell
python scripts\check_repo_purity.py
python scripts\check_versions.py
python scripts\build_plugin.py --check
python tests\acceptance\test_km_workflow.py
```

Acceptance writes only to temporary Vaults. Never point tests at the real user
config or Vault.
