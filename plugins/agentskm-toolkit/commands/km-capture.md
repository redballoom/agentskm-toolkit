---
description: Propose one reusable AgentsKM Inbox candidate
---

Use the `agentskm` Skill and the AgentsKM MCP server from this plugin.

Review the current conversation for durable, reusable knowledge. Capture only
verified technical solutions, debugging paths, architecture decisions, operating
procedures, tool comparisons, or corrected constraints that are likely to save
future work.

Workflow:

1. Search existing Wiki and Inbox entries for the same topic.
2. Do not capture secrets, credentials, customer data, personal data, or
   unverified guesses.
3. If there is meaningful new knowledge, call `km_propose_capture` to create one
   concise Inbox candidate.
4. Record `remind` when the MCP tools support it.
5. Ask the user to choose `沉淀 / 稍后 / 忽略` only after the main answer and
   only once for this candidate in this conversation. An explicit `记住这条`
   or `沉淀这条` names immediate capture intent and does not need a redundant
   confirmation.

After `沉淀`, follow the active Profile. A `contributor` records capture intent
and reports the exact Inbox path plus the pending reviewer/compiler role. A
`reviewer` records approval but cannot write Wiki. A `compiler` may promote to
an allowed Wiki target or additively merge into an existing page only when the
candidate is approved and safe; report the final Wiki path and whether it was
created or merged. On conflict, ambiguous target, missing evidence, safety
block, or missing tool/role, leave the candidate in Inbox and report the
blocker and next required role/tool. `稍后` defaults to seven days and must
report `snoozed_until`; `忽略` retains audit history.
