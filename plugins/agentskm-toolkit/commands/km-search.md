---
description: Search reviewed AgentsKM Wiki knowledge
argument-hint: [topic]
---

Use the AgentsKM MCP server from this plugin.

Search for knowledge related to: `$ARGUMENTS`

Workflow:

1. Call `km_search` with the requested topic.
2. Prioritize reviewed Wiki results.
3. Include Inbox results only when useful, and label them as unreviewed.
4. Summarize the most relevant matches with paths or candidate ids when
   available.

If no topic was provided, ask the user what to search for instead of guessing.
