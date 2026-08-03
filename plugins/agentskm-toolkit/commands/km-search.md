---
description: Search reviewed AgentsKM Wiki knowledge
---

Use the AgentsKM MCP server from this plugin.

Use this prompt when the user asks to search AgentsKM knowledge. Determine the
search topic from the user's request. If no topic is clear, ask a concise
follow-up question instead of guessing.

Workflow:

1. Call `km_search` with the requested topic once it is clear.
2. Prioritize reviewed Wiki results.
3. Include Inbox results only when useful, and label them as unreviewed.
4. Summarize the most relevant matches with paths or candidate ids when
   available.
