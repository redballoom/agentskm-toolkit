# AgentsKM Toolkit Architecture

> Status: current product architecture for the 0.5.x line

AgentsKM is a local, role-aware knowledge workflow for multiple Agent hosts.
It captures reusable results into a shared Inbox and promotes reviewed content
to a user-owned Wiki without placing knowledge data inside the Toolkit package
or plugin.

## System Boundary

```text
User conversation
  -> host integration
     -> Skill: when and why to use AgentsKM
     -> MCP: structured, role-filtered Agent tools
        -> CLI core: config, authorization, locks, transactions, audit
           -> user Vault: Inbox, Wiki, Raw, indexes, logs
```

The CLI core is the only business implementation. MCP, the Codex plugin, the
optional loopback HTTP adapter, and compatibility launchers must delegate to
that core rather than implement knowledge mutations themselves.

## Distribution Model

| Component | Distribution | Responsibility |
| --- | --- | --- |
| Python package | PyPI as `agentskm-toolkit` | CLI and stdio MCP runtime |
| Codex plugin | GitHub Marketplace | Skill, optional commands, MCP registration |
| Other Agent integration | Host MCP configuration | Starts the pinned PyPI runtime with a Profile |
| Vault | User filesystem | Private knowledge and audit data |

The Codex plugin is intentionally lightweight. Its MCP registration invokes:

```text
uvx --from agentskm-toolkit==<version> agentskm mcp ...
```

No end-user installation requires a repository clone or global Python package.
The stable Marketplace ref must only pin a version already available from
production PyPI.

## Runtime Source Of Truth

```text
src/agentskm_toolkit/          authoritative Python runtime
plugins/agentskm-toolkit/     lightweight Codex plugin
.agents/plugins/              repository Marketplace manifest
integrations/                 host-specific MCP examples
tests/acceptance/             isolated end-to-end tests
```

`tools/km-cli` and `adapters/mcp` are 0.5.x source-checkout compatibility
launchers. They contain no business logic and may only be removed through an
announced compatibility change. The HTTP adapter is optional and source-only;
it is not bundled by the plugin or advertised as a public network service.

## Configuration And Vault Resolution

The default configuration is `~/.agentskm/config.json`. The default Vault is
`~/Documents/AgentsKM/vault`. Environment variables are not a Vault selection
mechanism.

Configuration schema v1 separates Vault definitions from Agent identities:

```json
{
  "schema_version": 1,
  "default_profile": "codex",
  "vaults": {
    "main": {
      "path": "C:\\Users\\example\\Documents\\AgentsKM\\vault",
      "create_if_missing": false
    }
  },
  "profiles": {
    "codex": {
      "display_name": "Codex",
      "host": "codex",
      "actor_id": "codex",
      "role": "compiler",
      "vault": "main",
      "enabled": true
    },
    "hermes-agent": {
      "display_name": "Hermes",
      "host": "hermes",
      "actor_id": "hermes-agent",
      "role": "contributor",
      "vault": "main",
      "enabled": true
    }
  },
  "policies": {
    "review": {"separation_of_duties": false},
    "reminders": {"enabled": true, "default_snooze_days": 7}
  }
}
```

Vault paths must be absolute. Profile names select an identity; `actor_id` must
be unique, and each Profile references a configured Vault. Config, Profile,
Vault, or role conflicts fail closed instead of silently changing identity.

On first MCP start, missing configuration or a missing Profile is bootstrapped
using the explicit `--profile`, `--host`, and `--bootstrap-role` arguments. A
new compiler Profile requires an explicit trusted setup path. Setup, role, or
version changes require a new MCP connection.

## Roles And Enforcement

```text
contributor -> search, propose, respond
reviewer    -> contributor + review, dashboard
compiler    -> reviewer + promote, merge
```

MCP filters its tool list when the connection starts. The CLI independently
checks the selected Profile before every protected operation, so a host cannot
bypass authorization by invoking the command directly or inventing a role
argument.

User intent and quality review are separate records. A contributor can record
`capture`, `snooze`, or `reject`, but cannot approve content. A reviewer can
approve a sourced, non-secret candidate. Promotion or merge requires compiler
authority, candidate status `approved`, and explicit `approved_by` and `scope`
audit values.

## Knowledge State

```text
raw/          source material and evidence
000_Inbox/    unreviewed candidates and retained audit records
wiki/         reviewed knowledge
docs/         Vault-local operating or architecture notes
index.md      derived navigation
log.md        append-only operation audit
.km/          locks, cache, and transaction state
```

Wiki is preferred for reuse. Inbox results must be identified as unreviewed.
Graduated or merged Inbox files remain as audit records. Candidate schema,
status transitions, source requirements, and reminder rules are defined in
[agent-knowledge-protocol.md](agent-knowledge-protocol.md) and
[SCHEMA.md](../SCHEMA.md).

## Write Safety

- Agent-facing writes go through MCP tools; terminal recovery uses the same CLI.
- Repository-relative paths are normalized and constrained to the active Vault.
- Locks serialize competing writers.
- Transactions avoid partially updated candidate, Wiki, index, and log files.
- Fingerprints make repeated capture idempotent.
- Secret detection blocks unsafe candidates and promotion.
- `--dry-run` previews supported writes without changing the Vault.
- Tests always use temporary config and Vault paths.

The Toolkit repository, Python distribution, plugin, logs, and examples must
not contain a user Vault, user config, credentials, or private conversation
content.

## Updates And Connection Lifetime

The PyPI runtime cannot replace its own running process. Codex refreshes the
Git Marketplace snapshot and reinstalls the plugin; other hosts update the
exact package pin in MCP configuration. A new session or MCP reconnect then
loads the new runtime and role-filtered tool list.

`km_update` reports the appropriate next action. `km_doctor` is the final
runtime check for version, Profile, role, config, Vault, locks, state, and next
action.

## Stable Documentation

- [User guide index](guides/README.md)
- [Knowledge protocol](agent-knowledge-protocol.md)
- [Operations runbook](operations-runbook.md)
- [Development workflow](toolkit-development-workflow.md)
- [Release checklist](release-checklist.md)
- [Plugin UI migration gate](plugin-ui-migration-gate.md)

Completed implementation plans and release-closure notes belong in Git and PR
history, not in the current product documentation set.

`km dashboard` and `km qmd-readiness` generate reports inside the active user
Vault. Generated reports and their knowledge-specific links are Vault data and
must never be committed as Toolkit product documentation.
