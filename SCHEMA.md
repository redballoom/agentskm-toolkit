# AgentsKM Vault Schema

This document defines the portable Markdown contract used by AgentsKM 0.5.x.
It contains no user-specific domain taxonomy. A Vault may add its own purpose,
tag vocabulary, and content policies without changing the Toolkit runtime.

## Vault Layout

```text
vault/
  000_Inbox/       candidate knowledge and retained audit records
  raw/             optional source material
  wiki/            reviewed knowledge
    entities/
    concepts/
    comparisons/
    queries/
  docs/            generated dashboard and Vault-local operating notes
  index.md          generated Wiki navigation
  log.md            append-only operation audit
  .km/              locks, transactions, and derived cache
```

Markdown and frontmatter are the durable source of truth. Dashboard, indexes,
and caches are derived views and can be regenerated.

## File Conventions

- Use UTF-8 Markdown.
- Use lowercase, hyphenated filenames without spaces for generated pages.
- Store paths relative to the Vault in metadata and links.
- Update the `updated` date when content or review state changes.
- Do not directly edit candidate state to bypass CLI authorization or audit.

## Inbox Candidate

New candidates use frontmatter schema v1:

```yaml
---
id: kmc-YYYYMMDD-NNNN
title: Candidate title
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: pending
type: entity | concept | comparison | query | summary | note | guide
tags: [implicit-capture]
agent_id: agent-profile
source_tool: host-integration
source_session: stable-session-reference
source_refs:
  - conversation:session-reference
suggested_action: create | merge | hold | reject
suggested_target: wiki/concepts/candidate-title.md
value_reason: Why this result is reusable
confidence: high | medium | low
sensitivity: normal | sensitive
fingerprint: sha256-of-normalized-topic-and-claims
---
```

Optional workflow fields are written by CLI operations:

```yaml
user_decision: capture | snooze | reject | remind
responded_by: user-or-agent-id
responded_at: YYYY-MM-DD
review_decision: approve | snooze | reject | remind
reviewed_by: reviewer-id
reviewed_at: YYYY-MM-DD
review_reason: explanation
snoozed_until: YYYY-MM-DD
graduated_to: wiki/path.md
merged_to: wiki/path.md
```

Legacy `sources` may be read during migration, but new writes use
`source_refs`. A conversation-derived result uses a compact
`conversation:<session-reference>` source, not a complete transcript.

## Candidate States

| State | Meaning |
| --- | --- |
| `pending` | Captured and not yet surfaced |
| `pending-source-review` | Valuable but missing sufficient source evidence |
| `reminded` | Surfaced to the user; may also contain capture intent |
| `snoozed` | Deferred until `snoozed_until` |
| `approved` | Quality review passed |
| `duplicate` | Matches an existing candidate or Wiki page |
| `graduated` | Compiled into a new Wiki page |
| `merged` | Compiled into an existing Wiki page |
| `rejected` | Explicitly excluded from knowledge promotion |

`graduated`, `merged`, and `rejected` are terminal. Inbox files remain in place
as audit records.

## Wiki Page

```yaml
---
title: Reviewed knowledge title
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active | draft | archived
type: entity | concept | comparison | query | summary | note | guide
tags: [domain-defined-tag]
source_refs:
  - conversation:session-reference
origin_candidate: 000_Inbox/candidate-file.md
confidence: high | medium | low
---
```

A Vault may define stricter page templates and tag rules. Toolkit validation
requires the common fields but does not impose a personal or organizational
domain taxonomy.

## Raw Source

Raw files may use source metadata for drift and provenance:

```yaml
---
source_url: https://example.com/source
ingested: YYYY-MM-DD
sha256: body-content-digest
---
```

Raw evidence is not automatically treated as reviewed knowledge.

## Promotion Contract

A candidate can be promoted or merged only when:

- its status is `approved`;
- it has at least one `source_refs` entry;
- it is not marked or detected as secret;
- the selected Profile has compiler authority;
- the operation records explicit `approved_by` and `scope` values;
- the target remains inside `wiki/`.

Promotion updates the Wiki target, candidate audit state, `index.md`, and
`log.md` in one locked transaction.

## Sensitive Content

Never store credentials, access tokens, private keys, customer data, personal
data, or full private transcripts. Detection of secret-like content blocks
candidate creation or promotion; users must redact the source before retrying.

## Generated Vault Files

`agentskm dashboard` writes `docs/review-dashboard.md` by default.
`agentskm qmd-readiness` writes `docs/qmd-readiness.md` by default. These files
belong to the active user Vault and must not be copied into the public Toolkit
repository.

Role behavior and interaction rules are defined in
[docs/agent-knowledge-protocol.md](docs/agent-knowledge-protocol.md).
