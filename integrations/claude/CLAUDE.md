# AgentsKM Entry For Claude Code

Use the `agentskm` MCP server as the only write path for knowledge files.

- Search Wiki before repeating prior research.
- Treat Inbox results as unreviewed.
- Submit reusable, verified outcomes with `km_propose_capture`.
- Contributor profiles must not edit Wiki or Inbox Markdown directly.
- Tell the user which candidate was created and why it is valuable.
- A compiler profile may promote or merge only after the candidate is approved.

The canonical role, state, and content rules live in
`docs/agent-knowledge-protocol.md` in the toolkit repository.
