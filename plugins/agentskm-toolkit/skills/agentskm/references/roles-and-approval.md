# Roles And Approval

## Capability Matrix

| Role | Capabilities |
|---|---|
| contributor | setup status, doctor, update, status, search, validate, lint, pending, reminders, propose, respond |
| reviewer | contributor capabilities plus review and dashboard |
| compiler | reviewer capabilities plus promote and merge |

The MCP server derives the role from the selected Profile. Do not pass a role
override, manually edit Markdown, or use a shell command to bypass an absent
tool.

## Candidate State Flow

```text
pending-source-review -> pending -> reminded/capture-requested
pending/reminded/capture-requested -> snoozed/rejected/approved
approved -> graduated or merged
```

The CLI remains authoritative if a more precise state name is returned.

## Decisions

- Contributor: use `km_respond_candidate` for `remind`, `capture`, `snooze`, or
  `reject`. `capture` records user intent but does not approve.
- Reviewer/compiler: use `km_review_candidate` for `remind`, `approve`,
  `snooze`, or `reject`.
- Compiler: use `km_promote_candidate` for a new page or
  `km_merge_candidate` for an existing page, only after approval.

Promotion and merge require explicit `approved_by` and `scope` values tied to
the user's decision. Never graduate a pending candidate, invent approval, or
reinterpret a general request as approval for an unrelated candidate.

## Completion Reporting

- A successful contributor capture ends at `000_Inbox/<candidate>.md`; report
  that path and say that reviewer/compiler processing is pending.
- A successful compiler promotion or merge reports the final `wiki/...md` path,
  the returned `status`, and `operation` (`create_wiki_page` or
  `merge_wiki_page`).
- A snooze reports `snoozed_until`; when the user gives no date, use the
  seven-day default. A rejection reports the retained Inbox path.
- A missing role or tool is a boundary result, not a partial success. Explain
  what is unavailable and which role or reconnect is required.
- On a conflict, ambiguous target, missing evidence, or safety block, keep the
  candidate in Inbox and report its path and machine-readable blocker when
  available.
