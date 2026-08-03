# AgentsKM Slash-style Prompts

These are prompt conventions for Codex users and Agents. They are not a separate
runtime, and they do not bypass the MCP role model.

## `/km-doctor`

Purpose: diagnose the active AgentsKM package, Profile, role, config file, Vault
path, permissions, and setup state.

Expected Agent behavior:

1. Call `km_setup_status` when available.
2. Call `km_doctor`.
3. Explain the active Profile, role, config path, Vault path, and any required
   reconnect or setup action.

## `/km-capture`

Purpose: inspect the current conversation and create one Inbox candidate when it
contains reusable knowledge.

Expected Agent behavior:

1. Search for similar Wiki or Inbox entries first.
2. Create one concise candidate with `km_propose_capture` only when there is a
   durable, non-sensitive result.
3. Record `remind` when supported.
4. Ask the user to choose `沉淀 / 稍后 / 忽略`.

## `/km-search`

Purpose: search existing knowledge before repeating investigation.

Expected Agent behavior:

1. Search reviewed Wiki content first.
2. Include Inbox results only when useful, and label them as unreviewed.
3. Summarize results with source paths or candidate ids when available.

