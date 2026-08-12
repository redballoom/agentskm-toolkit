# Capture Workflow

## Candidate Gate

Capture only a verified, reusable result that is likely to reduce future work:

- a multi-step solution or debugging path;
- an architecture decision with its constraints and tradeoffs;
- an SOP, operating pattern, or meaningful tool comparison;
- corrected knowledge or an important applicability boundary.

Do not capture trivial mistakes, generic advice, incomplete exploration,
unverified guesses, one-off business fields, or sensitive content.

## Duplicate Check

Search the proposed topic before writing. Do not create a candidate when there
is no meaningful new claim. Suggest `merge` when an existing Wiki page covers
the subject; otherwise suggest a categorized Wiki target for `create`.

## Proposal

Call `km_propose_capture` with:

- a concise Chinese title and reusable body;
- a concrete `value_reason`;
- `conversation:<id>` in `source_refs` when no file evidence exists;
- the suggested action and a complete Vault-relative Wiki target such as
  `wiki/concepts/project-state-space.md`; include the `wiki/` prefix and `.md`,
  or omit `suggested_target` and let AgentsKM derive it from type and title;
- the real Agent, host tool, and session provenance;
- honest confidence and sensitivity values.

Inbox is shared by all Profiles using the same Vault. Preserve provenance via
`agent_id`, `source_tool`, `source_session`, and `source_refs`. Let the CLI
merge duplicate contributors and sessions instead of creating a second record.

After creation, record `remind` with `km_respond_candidate` as a contributor or
`km_review_candidate` as reviewer/compiler, then show the compact user choice
prompt from `SKILL.md`. This is the only capture prompt for the conversation;
do not repeat it for the same candidate and state.

## User Choice

- `沉淀`: contributor records `capture` and reports the candidate's exact
  `000_Inbox/...` path plus `reviewer-or-compiler` as the next role. A
  reviewer/compiler records `approve`; only a compiler may then call promote
  or merge after status is `approved`, and must report the final `wiki/...`
  path and whether it created or merged a page.
- `稍后`: record `snooze` with the user's date, or seven days when none is
  supplied. Report the resulting `snoozed_until` date and candidate path.
- `忽略`: record `reject`; retain the Inbox record for audit history and report
  its path and rejected status.

A user request counts as approval only when it clearly names the candidate or
directly answers the immediately preceding proposal. Never invent approval.

For a contributor capture response, `status: reminded` is the compatible Inbox
workflow state. Use `intent_status: capture_requested`, `user_decision:
capture`, and `next_action: await_review` when explaining the result to the
user; do not describe it as merely reminded.

If the required role or MCP tool is unavailable, report the active boundary and
the next required role/tool. Do not claim that the candidate reached Wiki.
Compiler conflicts, ambiguous targets, missing evidence, or safety failures
leave the candidate in Inbox; report the blocker and Inbox path.
