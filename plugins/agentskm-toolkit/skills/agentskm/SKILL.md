---
name: agentskm
description: Manage a local multi-agent AgentsKM knowledge Vault through its MCP tools. Use for first-time setup, configuration or doctor checks, Profile and Vault selection, role or permission questions, searching prior Wiki knowledge, detecting reusable conversation outcomes, proposing Inbox candidates, reminding or postponing a candidate, ignoring or rejecting knowledge, reviewing candidates, and promoting or merging approved knowledge. Trigger when users mention AgentsKM, knowledge capture, knowledge deposition, Inbox, Wiki, Vault, remember this, save this for later, search prior experience, 沉淀, 稍后, 忽略, 审核, 毕业, or 合并, and when a technical conversation produces a verified reusable solution, debugging path, architecture decision, SOP, comparison, or corrected constraint.
---

# AgentsKM

Use the `agentskm` MCP server as the Agent-facing interface. Wiki pages are
reviewed knowledge; Inbox candidates are unreviewed proposals.

## Core Rules

- Keep normal work quiet. Do not narrate MCP startup, Profile, Vault, searches,
  or internal state unless the user asks or an operation needs attention.
- Call MCP tools instead of editing Vault Markdown or user configuration.
- Let the packaged CLI enforce roles, paths, locks, transactions, safety checks,
  and audit records.
- Never bypass a missing tool, role boundary, candidate state, or approval
  requirement. Never persist credentials, private data, or unsupported claims.
- Use only the Profile and Vault reported by Setup or Doctor.

## Route The Request

1. For setup, Profile, role, Vault, startup, or health questions, call
   `km_setup_status`, then `km_doctor`. Read
   [setup-and-profiles.md](references/setup-and-profiles.md) when setup is not
   ready.
2. For reusable prior knowledge, call `km_search`; rank Wiki above Inbox and
   label Inbox results as unreviewed.
3. For a durable result from this conversation, follow
   [capture-workflow.md](references/capture-workflow.md).
4. For remind, snooze, reject, approve, promote, or merge actions, follow
   [roles-and-approval.md](references/roles-and-approval.md).

## Quiet Capture

Do not capture or prompt for trivial, exploratory, one-off, unverified, or
duplicate content. A candidate must be verified, reusable, non-secret, and
likely to reduce future work.

When the user explicitly says `记住这条` or `沉淀这条`, treat it as intent for
the immediately named result. Do not ask a redundant confirmation. Still run
the normal duplicate, evidence, safety, target, and Profile checks.

Otherwise create at most one candidate prompt per conversation, after the main
answer and only when the result passes the candidate gate:

```text
发现一条值得保存的知识：{title}
价值：{value_reason}
请选择：沉淀 / 稍后 / 忽略
```

Do not repeat a prompt for a candidate already reminded in the same state.
Use `km_reminders` only for new or due candidates.

## Permission-Aware Completion

After the user chooses, act only within the active Profile:

| Profile | `沉淀` / `记住这条` | Completion message |
|---|---|---|
| `compiler` | Review, then promote or additive-merge when safe and in scope | Report the final Wiki path and whether it was created or merged |
| `contributor` | Record capture intent and keep the candidate in Inbox | Report the Inbox path and that reviewer/compiler action is pending |

`稍后` uses the requested date or a seven-day default. `忽略` rejects the
candidate but retains its audit record. Always include the final status and
path when a write succeeds. If a compiler operation is blocked by a conflict,
ambiguous target, missing evidence, or safety check, leave the candidate in
Inbox and report the blocker and candidate path.

## Tool Availability

The MCP tool list is fixed for the current connection. After setup, Profile or
role changes, or an update, honor `reconnect_required` and ask the host to
reconnect. If a required tool is absent, explain the active boundary briefly;
do not promise a Wiki result from a contributor session.
