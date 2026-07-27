---
name: agentskm-capture
description: Manage a local AgentsKM knowledge vault during technical and workflow conversations. Use when a conversation may contain reusable solutions, debugging paths, architecture decisions, tool comparisons, operating procedures, corrections to existing knowledge, or when the user asks to search, remember, defer, ignore, review, merge, or promote knowledge in AgentsKM.
---

# AgentsKM Capture

Use the `agentskm` MCP tools. Treat Wiki as reviewed knowledge, Inbox as unreviewed candidates, and Raw as evidence.

## Start Of Work

1. Search Wiki when the task could benefit from prior reusable knowledge.
2. Clearly label Inbox results as unreviewed.
3. Continue normally if AgentsKM is unavailable; mention the missing connection only when it affects the requested workflow.

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
