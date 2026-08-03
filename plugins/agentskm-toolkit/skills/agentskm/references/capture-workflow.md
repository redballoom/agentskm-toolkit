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
- the suggested action and Wiki target;
- the real Agent, host tool, and session provenance;
- honest confidence and sensitivity values.

Inbox is shared by all Profiles using the same Vault. Preserve provenance via
`agent_id`, `source_tool`, `source_session`, and `source_refs`. Let the CLI
merge duplicate contributors and sessions instead of creating a second record.

After creation, record `remind` with `km_respond_candidate` as a contributor or
`km_review_candidate` as reviewer/compiler, then show the compact user choice
prompt from `SKILL.md`.

## User Choice

- `沉淀`: contributor records `capture`; reviewer/compiler records `approve`.
  Only a compiler may then call promote or merge after status is `approved`.
- `稍后`: record `snooze` with the user's date, or seven days when none is
  supplied.
- `忽略`: record `reject`; retain the Inbox record for audit history.

A user request counts as approval only when it clearly names the candidate or
directly answers the immediately preceding proposal. Never invent approval.
