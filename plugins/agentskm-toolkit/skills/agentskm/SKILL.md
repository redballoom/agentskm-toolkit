---
name: agentskm
description: Manage a local multi-agent AgentsKM knowledge Vault through its MCP tools. Use for first-time setup, configuration or doctor checks, Profile and Vault selection, role or permission questions, searching prior Wiki knowledge, detecting reusable conversation outcomes, proposing Inbox candidates, reminding or postponing a candidate, ignoring or rejecting knowledge, reviewing candidates, and promoting or merging approved knowledge. Trigger when users mention AgentsKM, knowledge capture, knowledge deposition, Inbox, Wiki, Vault, remember this, save this for later, search prior experience, 沉淀, 稍后, 忽略, 审核, 毕业, or 合并, and when a technical conversation produces a verified reusable solution, debugging path, architecture decision, SOP, comparison, or corrected constraint.
---

# AgentsKM

Use the `agentskm` MCP server as the Agent-facing interface. Treat Wiki pages
as reviewed knowledge and Inbox candidates as unreviewed proposals.

## Core Rules

- Call MCP tools instead of editing Vault Markdown or user configuration.
- Let the packaged CLI enforce Profile roles, paths, locks, transactions,
  frontmatter, sensitive-content checks, and audit records.
- Never bypass a missing tool, role boundary, candidate state, or explicit
  approval requirement.
- Never persist credentials, secrets, customer data, personal data, or
  unsupported claims.
- Use only the Profile and Vault reported by Setup or Doctor. Do not infer a
  path from environment variables or a source checkout.

## Route The Request

1. For installation, configuration, Profile, role, Vault, startup, or health
   questions, call `km_setup_status` and then `km_doctor`. Read
   [setup-and-profiles.md](references/setup-and-profiles.md) when setup is not
   ready or the Profile needs to change.
2. For prior knowledge, call `km_search`. Prioritize Wiki results and clearly
   label Inbox results as unreviewed.
3. For a reusable result from the current conversation, search for duplicates,
   then follow [capture-workflow.md](references/capture-workflow.md).
4. For remind, snooze, reject, approve, promote, or merge actions, read
   [roles-and-approval.md](references/roles-and-approval.md) before calling a
   write tool.

## Conversation Workflow

At the start of work, search Wiki when prior reusable knowledge could reduce
repeated investigation. Do not force a knowledge-base lookup for unrelated or
trivial requests.

Before the final answer, evaluate whether the conversation produced a durable,
verified result. When it did, create at most one concise candidate and place
the review prompt after the main answer:

```text
发现一条值得沉淀的知识：{title}
价值：{value_reason}
建议：{create|merge} -> {target}
请选择：沉淀 / 稍后 / 忽略
```

Do not repeatedly prompt for a candidate already marked `reminded`. Surface
only new or due candidates returned by `km_reminders`.

## Tool Availability

Treat the MCP tool list as fixed for the current connection. After Setup,
Profile changes, role changes, or an AgentsKM update, honor
`reconnect_required` and ask the host to reconnect the MCP server or start a
new conversation. Never terminate the host process from this Skill.

If a required tool is absent, state the active role boundary and leave the
candidate in its current state. A contributor records user capture intent but
does not approve or graduate knowledge.
