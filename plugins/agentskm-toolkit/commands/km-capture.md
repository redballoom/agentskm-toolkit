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
5. Ask the user to choose `沉淀 / 稍后 / 忽略`.

Do not approve, promote, or merge without the user's explicit decision and the
required role permissions.
