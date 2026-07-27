---
name: agentskm-capture
description: Set up and manage a local AgentsKM knowledge vault during technical and workflow conversations. Use when AgentsKM is newly installed or unconfigured, when an Agent Profile or Vault connection must be checked, or when a conversation may contain reusable solutions, debugging paths, architecture decisions, tool comparisons, operating procedures, corrections to existing knowledge, or the user asks to search, remember, defer, ignore, review, merge, or promote knowledge.
---

# AgentsKM Capture

Use the `agentskm` MCP tools. Treat Wiki as reviewed knowledge, Inbox as unreviewed candidates, and Raw as evidence.

## Setup And Bootstrap

When `km_setup_status` is available, call it before the first knowledge-base operation in a new installation or after a setup-related error.

If it reports `configured: true`, use the normal tools exposed for the selected Profile. Do not ask the user to configure the Vault again.

If only `km_setup_status` and `km_setup_instructions` are available, the MCP server is intentionally in read-only Bootstrap mode:

1. Call both tools and explain the reported state.
2. Reuse an existing configured Vault when one is listed. Otherwise ask for the absolute path of an existing AgentsKM Vault.
3. Use the Profile requested by the host. Recommend `contributor` for Hermes, Claude, Cursor, automation, and other new Agents. A `compiler` Profile requires explicit user confirmation.
4. Show the exact Profile, role, Vault name, Vault path, and config path that Setup will change.
5. Ask for confirmation before changing the user configuration.
6. After confirmation, use a local shell to run the bundled `km.py setup` CLI reported by `km_setup_instructions`. Use `--confirm-compiler` only when the user explicitly approved a Compiler Profile.
7. Report the CLI result and ask the user to restart the Agent or reconnect the MCP server. Do not claim the full tool set is active in the current MCP process.

The CLI is the only Setup writer. Never edit `%USERPROFILE%/.agentskm/config.json` directly and never invent an MCP configuration-writing call. Repeated Setup is idempotent; an existing conflicting Profile must be shown to the user rather than overwritten.

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

After the candidate is created, record `remind` with `km_review_candidate`, then append this compact prompt to the user-facing answer:

```text
发现一条值得沉淀的知识：{title}
价值：{value_reason}
建议：{create|merge} -> {target}
请选择：沉淀 / 稍后 / 忽略
```

Do not interrupt the main answer with the prompt. Do not repeatedly remind a candidate whose status is `reminded`. Only surface candidates returned by `km_reminders`.

## Apply User Decision

- `沉淀`: record `approve`, then call `km_promote_candidate` for a new page or `km_merge_candidate` for an existing page. Pass explicit approval metadata tied to the user's message.
- `稍后`: record `snooze` with a concrete `until` date. Use seven days when the user gives no date.
- `忽略`: record `reject`; do not delete the Inbox record.

Never promote or merge before status becomes `approved`. Never invent approval. A request to capture is approval only when it clearly refers to the named candidate or the immediately preceding proposal.

## Permissions

Contributor profiles may search and propose. Reviewer profiles may also record review decisions. Compiler profiles may promote or merge approved candidates. If the required tool is absent, report the current role boundary and leave the candidate in its existing state.

Do not bypass a missing MCP capability by editing Markdown directly.
