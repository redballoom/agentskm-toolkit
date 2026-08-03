---
name: agentskm-capture
description: Set up and manage a local AgentsKM knowledge vault during technical and workflow conversations. Use when AgentsKM is newly installed or unconfigured, when an Agent Profile or Vault connection must be checked, when the user asks to diagnose AgentsKM, capture reusable knowledge, or search the Vault, or when a conversation may contain reusable solutions, debugging paths, architecture decisions, tool comparisons, operating procedures, corrections to existing knowledge, or the user asks to remember, defer, ignore, review, merge, or promote knowledge.
---

# AgentsKM Capture

Use the `agentskm` MCP tools. Treat Wiki as reviewed knowledge, Inbox as unreviewed candidates, and Raw as evidence.

## Setup And Bootstrap

On the first MCP start after installation, AgentsKM automatically creates
`%USERPROFILE%/.agentskm/config.json`, the requested Agent Profile, and an empty
Vault at `%USERPROFILE%/Documents/AgentsKM/vault` when no config exists. The
empty Vault includes its layer directories and local usage instructions.

When `km_setup_status` is available, call it before the first knowledge-base operation in a new installation or after a setup-related error. Use `km_doctor` when the state or path is unclear.

If it reports `configured: true`, use the normal tools exposed for the selected Profile. Do not ask the user to configure the Vault again.

If only Setup, Doctor, and Update tools are available, automatic bootstrap could not safely complete, usually because the config is legacy/invalid or a target directory is non-empty:

1. Call both tools and explain the reported state.
2. Reuse an existing configured Vault when one is listed. Otherwise use the recommended default path unless the user asks for another Vault.
3. Use the Profile requested by the host. Recommend `contributor` for Hermes, Claude, Cursor, automation, and other new Agents. A `compiler` Profile requires explicit user confirmation.
4. Show the exact Profile, role, Vault name, Vault path, and config path that Setup will change.
5. Use a local shell to run the exact packaged CLI command reported by `km_setup_instructions`. The plugin runtime is resolved from PyPI through `uvx`; do not look for a bundled `km.py`. Use `--confirm-compiler` only when the user explicitly approved a Compiler Profile.
6. Call `km_setup_status` again. Setup and Vault path changes are re-read on each operation and do not normally require an Agent restart.

The CLI is the only Setup writer. Never edit `%USERPROFILE%/.agentskm/config.json` directly and never invent an MCP configuration-writing call. Repeated Setup is idempotent; an existing conflicting Profile must be shown to the user rather than overwritten. Do not use environment variables to select the config, Profile, role, or Vault.

## Diagnose And Update

- Use `km_doctor` when installation, Profile, role, config, Vault, permissions, or stale locks may be wrong.
- When the user asks to update AgentsKM, call `km_update` directly; do not add another confirmation prompt.
- A code update returns `restart_required: true`. Ask the host to reconnect this MCP server when supported; otherwise tell the user to start a new conversation. Never terminate the active host process from the Skill.

## Prompt Shortcuts

Treat `/km-doctor`, `/km-capture`, and `/km-search` as text shortcuts for this
Skill when the host supplies them. They are prompt-backed compatibility files,
not a separate command runtime or a guaranteed visible slash-command menu.

- `/km-doctor`: call `km_setup_status` when available, then `km_doctor`, and report the active Profile, role, config path, Vault path, and next action.
- `/km-capture`: evaluate the current conversation, search for duplicates, propose one reusable Inbox candidate when appropriate, then ask `沉淀 / 稍后 / 忽略`.
- `/km-search <topic>`: search reviewed Wiki content first, then include Inbox results only when useful and clearly label them as unreviewed.

Do not treat slash commands as permission escalation. All role boundaries
and approval requirements still apply.

## Start Of Work

1. Search Wiki when the task could benefit from prior reusable knowledge.
2. Clearly label Inbox results as unreviewed.
3. If AgentsKM is unavailable because Setup is incomplete, follow the Bootstrap flow instead of guessing a Vault path.

## Capture Decision

Before the final answer, evaluate whether the conversation produced a durable result. Capture only:

- verified multi-step solutions or debugging paths;
- reusable architecture decisions, SOPs, patterns, or tool comparisons;
- corrected knowledge, changed constraints, or important applicability boundaries;
- conclusions likely to reduce repeated exploration in future work.

Do not capture secrets, credentials, customer data, personal data, trivial mistakes, unverified guesses, or one-off business fields.

Search for the proposed topic first. Prefer `merge` when an existing Wiki page covers the same subject. Do not propose when there is no meaningful new claim.

## Propose And Ask

Create one concise Inbox candidate with `km_propose_capture`. Include:

- a Chinese title and body;
- why it is reusable;
- the current task or conversation identifier as `conversation:<id>` in `source_refs` when no file evidence exists;
- a suggested Wiki target;
- the actual Agent and source tool identifiers;
- an honest confidence and sensitivity classification.

After the candidate is created, record `remind` with `km_respond_candidate` when available. If only `km_review_candidate` is available because the Profile is reviewer or compiler, use `km_review_candidate --decision remind`. Then append this compact prompt to the user-facing answer:

```text
发现一条值得沉淀的知识：{title}
价值：{value_reason}
建议：{create|merge} -> {target}
请选择：沉淀 / 稍后 / 忽略
```

Do not interrupt the main answer with the prompt. Do not repeatedly remind a candidate whose status is `reminded`. Only surface candidates returned by `km_reminders`.

Inbox is shared by all Profiles connected to the Vault. Keep provenance at the
top of every candidate through `agent_id`, `source_tool`, `source_session`, and
`source_refs`. On a duplicate candidate, preserve all contributing Agents and
sessions rather than creating a second record.

## Apply User Decision

- `沉淀`: record `approve`, then call `km_promote_candidate` for a new page or `km_merge_candidate` for an existing page. Pass explicit approval metadata tied to the user's message.
- `稍后`: record `snooze` with a concrete `until` date. Use seven days when the user gives no date.
- `忽略`: record `reject`; do not delete the Inbox record.

Never promote or merge before status becomes `approved`. Never invent approval. A request to capture is approval only when it clearly refers to the named candidate or the immediately preceding proposal.

## Permissions

Contributor profiles may search, propose, and record contributor-safe responses with `km_respond_candidate` (`remind`, `capture`, `snooze`, `reject`). Reviewer profiles may also approve candidates with `km_review_candidate`. Compiler profiles may promote or merge approved candidates. If the required tool is absent, report the current role boundary and leave the candidate in its existing state.

Do not bypass a missing MCP capability by editing Markdown directly.
