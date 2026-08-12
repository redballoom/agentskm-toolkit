# Permission-Aware Knowledge Capture Improvement Plan

> Status: implementation and automated acceptance complete; real-host pilot in progress
> Date: 2026-08-05
> Scope: AgentsKM Codex plugin, Skill instructions, MCP adapter responses,
> candidate safety checks, and real-host acceptance

## 0. Implementation Progress

| Step | Status | Result |
|---|---|---|
| 1. Freeze interaction contract | Complete | Compiler/contributor outcomes, conflict policy, final path reporting, and seven-day snooze are documented |
| 2. Refine AgentsKM Skill | Complete | Quiet capture, explicit intent, one-prompt limit, role branches, blockers, and reconnect behavior are defined in the Skill and references |
| 3. Improve MCP responses | Complete | Candidate operations return status, path/target, operation, next action, next role, snooze date, and blocker codes |
| 4. Add body safety scanning | Complete | Title, value reason, and body are scanned before proposal, approval, promotion, and merge |
| 5. Verify cron and Obsidian behavior | Codex host installed; observation pending | Reminder payloads remain metadata-only, snooze due behavior and Dashboard generation pass acceptance; Codex 0.5.3 local host installation is verified |
| 6. Run a one-week pilot | In progress | Codex explicit compiler capture and Hermes contributor/Hook capture have completed; longer observation remains |

Verification on 2026-08-05:

- `python -m py_compile src/agentskm_toolkit/km.py src/agentskm_toolkit/mcp.py tests/acceptance/test_km_workflow.py`
- `python tests/acceptance/test_km_workflow.py` -> `Acceptance workflow passed.`
- lightweight plugin check passed with `SKILL.md` at 77 lines;
- body secret rejection, ordinary token-refresh text, contributor handoff,
  compiler promotion/merge results, default snooze date, and MCP role blockers
  are covered by acceptance assertions.
- local Codex marketplace `agentskm-local` installed plugin version `0.5.3`;
- installed Skill hash matches the repository Skill, and the installed MCP
  runtime resolves `dist/agentskm_toolkit-0.5.3-py3-none-any.whl`;
- real-host `doctor` reports Profile `codex`, role `compiler`, the configured
  user Vault, and state `ready`.
- Hermes `0.5.3` completed the contributor capture flow and an implicit Hook
  capture. The pilot found that `suggested_target` needed an explicit
  `wiki/<category>/<slug>.md` contract and actionable validation guidance.

## 1. Objective

Make knowledge capture feel nearly invisible during normal work while keeping
the result deterministic and permission-aware:

```text
normal conversation
  -> only high-value verified results become candidates
  -> user says "沉淀" / "稍后" / "忽略"
  -> the active Profile performs only its permitted action
  -> the user receives the final status and filesystem location
```

The system must never make the user learn the Inbox/Wiki state machine in order
to use the basic habit. The state machine remains visible in review and
diagnostic workflows, not in every conversation.

## 2. Confirmed Interaction Contract

### 2.1 Permission-aware outcomes

| Active Profile | User intent | Permitted result | User-facing completion |
|---|---|---|---|
| `compiler` | `沉淀` / `记住这条` | Search for duplicates, review, then promote or merge when safe and in scope | Report Wiki path and whether the page was created or merged |
| `compiler` | `稍后` | Snooze the candidate using the requested date or the seven-day default | Report the next reminder date |
| `compiler` | `忽略` | Reject the candidate and retain its audit record | Report that it was ignored and retained |
| `contributor` | `沉淀` / `记住这条` | Create or update an Inbox candidate and record `capture` intent | Report Inbox path and that reviewer/compiler action is pending |
| `contributor` | `稍后` | Snooze the candidate | Report the next reminder date |
| `contributor` | `忽略` | Reject the candidate and retain its audit record | Report that it was ignored and retained |

`沉淀` is a one-time decision for the immediately preceding, clearly named
candidate. It is not permanent authorization for unrelated future candidates.
An explicit user request such as `记住这条` can skip a second capture question,
but still goes through the active Profile's permission checks.

### 2.2 Compiler conflict policy

The `compiler` Profile may complete the operation automatically only when all
of the following are true:

- the candidate has a source reference;
- the candidate is non-secret and passes content safety checks;
- the target is inside an allowed Wiki directory;
- an existing page is either absent or the candidate is an additive update;
- the operation is within the user's explicit decision scope.

If the candidate conflicts with an existing Wiki claim, would overwrite
existing content, has an ambiguous target, or lacks evidence, it remains in
Inbox. The Agent must report the blocking reason and the candidate path instead
of guessing.

### 2.3 Prompt policy

Default behavior is quiet:

- do not announce MCP startup, Profile, Vault, or every search;
- do not prompt for trivial, exploratory, unverified, or one-off content;
- create at most one capture prompt per conversation;
- prompt only for a verified, reusable, non-duplicate result;
- place the prompt after the main answer;
- do not repeat a prompt for a candidate already reminded in the same state;
- show implementation details only when the user asks or an operation fails.

Preferred prompt:

```text
发现一条值得保存的知识：{title}
价值：{value_reason}
请选择：沉淀 / 稍后 / 忽略
```

The prompt may add a short risk or evidence line when confidence is low or the
source needs attention. It should not expose internal role names by default.

## 3. Current Gaps

### P0: User-visible completion is not explicit enough

The current protocol correctly separates contributor capture intent from review
approval, but the Skill does not make the final user-facing branch explicit
enough. A user may not know whether `沉淀` produced an Inbox candidate or a Wiki
page.

### P0: Skill behavior is not fully deterministic across hosts

The current Skill describes the desired behavior, but several important rules
are model-enforced rather than runtime-enforced:

- one prompt per conversation;
- direct capture requests skipping redundant confirmation;
- compiler completion after an approved capture;
- the exact final status and path message.

### P0.5: Body-level sensitive-content protection is incomplete

The runtime checks the declared sensitivity value, but the capture path needs a
shared scan of candidate title, value reason, and body. The scan should block a
write on a high-confidence secret pattern and return a remediation message.

### P1: MCP results need clearer next actions

The current tool set is sufficient, but structured responses can better expose
`status`, `next_action`, `next_required_role`, final Wiki path, and blocking
reasons. This reduces the amount of state-machine interpretation required from
the Skill.

### P1: Real-host behavior is not fully covered

Core acceptance tests cover the CLI and MCP state machine. Additional tests are
needed for Codex and Hermes conversation behavior, weekly reminders, cron
payload privacy, duplicate prompts, and Obsidian review flow.

## 4. Implementation Sequence

### Step 1 - Freeze the interaction contract

**Goal:** establish one source of truth for what each Profile does after each
user decision.

**Changes:**

- add the permission-aware outcome table to the Skill references;
- define the compiler additive-merge and conflict-stop rules;
- define the four final response forms: Wiki, Inbox, snoozed, rejected;
- define that direct `记住这条` is explicit intent for the current candidate;
- define that `稍后` defaults to seven days;
- define that all compiler writes record `approved_by` and `scope`.

**Acceptance:**

- a contributor never promises Wiki completion;
- a compiler never reports success without a final path;
- a conflict produces a retained Inbox candidate and a clear blocker.

### Step 2 - Refine the AgentsKM Skill

**Files:**

- `plugins/agentskm-toolkit/skills/agentskm/SKILL.md`
- `plugins/agentskm-toolkit/skills/agentskm/references/capture-workflow.md`
- `plugins/agentskm-toolkit/skills/agentskm/references/roles-and-approval.md`
- `plugins/agentskm-toolkit/commands/km-capture.md`

**Changes:**

- add quiet-mode rules and explicit-capture rules;
- add a contributor/compiler behavior table;
- add the post-decision action sequence for compiler;
- require the final result path in every successful write response;
- prohibit setup/status narration during ordinary work;
- define when a prompt is not justified;
- define the response when a required role or tool is unavailable;
- keep the Skill short and move detailed state rules into references.

**Acceptance scenarios:**

1. Trivial conversation: no candidate and no prompt.
2. Verified technical solution: one candidate and one prompt.
3. Duplicate result: no second candidate; explain merge or existing match.
4. User says `沉淀` in Codex: review, promote/merge, and report Wiki path.
5. User says `沉淀` in Hermes: record capture intent and report Inbox path.
6. User says `记住这条`: no redundant confirmation.
7. User says `稍后`: report the calculated reminder date.
8. User says `忽略`: report rejection while retaining audit history.

### Step 3 - Improve MCP structured responses

**Files:**

- `src/agentskm_toolkit/mcp.py`
- focused MCP acceptance tests in `tests/acceptance/test_km_workflow.py`

**Changes:**

- preserve the current role-filtered tool list;
- do not add a general-purpose auto-workflow tool;
- add or normalize `next_action` in candidate response payloads;
- return `next_required_role` after contributor capture;
- return `target`, `operation`, and final `status` after promote/merge;
- return machine-readable blocker codes where practical;
- keep human-readable errors concise enough for direct Agent responses.

**Acceptance:**

- the Skill can answer "where did it go?" from the tool result alone;
- role changes still require reconnect;
- contributor MCP tools still exclude review, promote, and merge;
- compiler MCP tools retain the complete permitted set.

### Step 4 - Add shared body safety scanning

**Files:**

- `src/agentskm_toolkit/km.py`
- focused safety tests in `tests/acceptance/test_km_workflow.py`
- protocol documentation if the field or error contract changes

**Changes:**

- scan title, value reason, and body before Inbox persistence;
- scan again before approval and compiler writes as defense in depth;
- block high-confidence patterns such as private keys, bearer tokens, and
  known package or provider token formats;
- do not silently redact technical content;
- report the candidate was not written and ask for a sanitized version;
- keep `sensitivity` as an explicit metadata field in addition to scanning.

**Acceptance:**

- metadata `secret` is rejected;
- secret-like body content is rejected even when metadata says `normal`;
- ordinary words such as `token refresh` are not falsely rejected;
- no rejected body is written to Inbox, audit logs, or outbound reminders.

### Step 5 - Verify cron and Obsidian behavior

**Changes:**

- make weekly reminder payloads metadata-only by default;
- ensure repeated cron execution is idempotent;
- use `km_reminders` as the only source for due candidates;
- use `km_dashboard` as the Obsidian review entry point;
- document that direct Markdown edits can bypass audit and state protections.

**Acceptance:**

- a due candidate is not repeatedly sent in one reminder cycle;
- a snoozed candidate reappears only after its due date;
- reminder output does not expose candidate body or secrets;
- Dashboard links point to the correct Inbox and Wiki paths.

### Step 6 - Run a one-week pilot

**Observe:**

- candidate count per technical conversation;
- prompt acceptance, snooze, and rejection rates;
- duplicate candidate rate;
- time from Inbox to Wiki;
- compiler conflict rate;
- false-positive safety blocks;
- user-perceived interruption frequency.

**Decision rule:**

- if prompts are frequently rejected, raise the candidate gate;
- if candidates are rarely processed, improve the weekly review flow;
- if search quality is poor at current Vault size, improve ranking before adding
  an index;
- only add SQLite or vector search after measured search latency or quality
  justifies it.

## 5. Non-Goals

- no new personal compiler Profile for the current single-user workflow;
- no direct Obsidian write path;
- no vector database or memory layer;
- no Basic Memory reimplementation;
- no redesign of the CLI-owned state machine;
- no automatic permanent authorization for future candidates;
- no automatic conflict resolution that overwrites existing Wiki claims.

## 6. Definition Of Done

This improvement is complete when:

- the same Skill contract works for both compiler and contributor hosts;
- normal conversations remain quiet;
- high-value conversations produce at most one actionable prompt;
- compiler completion produces a Wiki path or a clear Inbox blocker;
- contributor completion produces an Inbox path and next responsible role;
- sensitive body content is blocked before persistence;
- cron and Dashboard behavior are verified against a disposable Vault;
- the existing CLI/MCP acceptance suite and new interaction tests pass;
- no user Vault data, credentials, or machine-specific paths enter the repo.

## 7. Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-08-05 | Use the existing Codex `compiler` Profile for the personal workflow | Avoid a second Profile and preserve current role boundaries |
| 2026-08-05 | `compiler` may complete safe, in-scope Wiki promotion after explicit capture intent | Make "沉淀" a low-friction action without granting permanent authorization |
| 2026-08-05 | `contributor` stops at Inbox | Enforce separation between contribution and formal knowledge publication |
| 2026-08-05 | Report the final path after every successful action | Remove ambiguity about where the knowledge was stored |
| 2026-08-05 | Default reminder delay is seven days | Keep the habit lightweight and avoid daily interruption |
| 2026-08-05 | Body safety scanning is the next security improvement | Metadata-only protection is insufficient once multiple channels share candidates |
| 2026-08-12 | Desktop hosts without a reliable lifecycle Hook use explicit user capture; Hermes CLI may run automatic capture assessment through its Hook | Preserve predictable desktop interaction while testing low-friction automation only where the host exposes a real event boundary |
| 2026-08-12 | Keep persisted contributor capture status `reminded`, but expose `intent_status: capture_requested` | Preserve the 0.5.x state machine while giving hosts an unambiguous user-facing state |
