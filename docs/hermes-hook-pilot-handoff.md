# Hermes Hook Pilot Handoff

> Status: Hermes local pilot in progress
> Toolkit version: `0.5.3`
> Last updated: 2026-08-12

This document gives a Hermes Agent enough context to continue the AgentsKM
Hook and end-to-end integration pilot without treating the repository as a
source of user Vault data or credentials.

## 1. Current State

AgentsKM is a local, role-aware knowledge workflow. It keeps unreviewed
knowledge in a shared Inbox and moves reviewed knowledge into a user-owned
Wiki. The Python CLI is the only business implementation; MCP and host
integrations are thin adapters.

```text
User conversation
  -> host integration
     -> Skill: semantic capture policy
     -> host Hook (when available): reliable evaluation timing
     -> MCP: role-filtered operations
        -> AgentsKM CLI: safety, state, locks, transactions, audit
           -> user Vault: 000_Inbox, wiki, raw, index, log
```

The release contract keeps `0.5.3` aligned in `pyproject.toml`,
`src/agentskm_toolkit/__init__.py`, the Codex plugin manifest, and the MCP
runtime pin. After the release is verified on PyPI, use
`agentskm-toolkit==0.5.3` for normal Hermes installation. A local wheel is only
a development fallback before publication or while testing unreleased changes;
never copy its machine-specific absolute path into source-controlled product
configuration.

## 2. Product Contract

Normal work should be quiet. A capture candidate is justified only when the
result is all of the following:

- verified rather than exploratory or speculative;
- reusable beyond the immediate one-off task;
- non-sensitive and free of credentials, private data, or customer data;
- supported by source evidence or a conversation reference;
- not already represented by a materially equivalent Wiki or Inbox item.

At most one capture prompt may be shown for a conversation:

```text
发现一条值得保存的知识：{title}
价值：{value_reason}
请选择：沉淀 / 稍后 / 忽略
```

An explicit request such as `记住这条`, `沉淀这条`, or `此次会话很有价值，需要沉淀`
is immediate user intent. It skips a redundant confirmation but never skips
duplicate, source, safety, target, or authorization checks.

### Permission boundary

| Profile | After user chooses `沉淀` | Required completion message |
| --- | --- | --- |
| `compiler` | Review, then safely promote or additive-merge | Wiki path and whether it was created or merged |
| `contributor` | Keep the candidate in Inbox and record capture intent | Inbox path and that reviewer/compiler action is pending |

Hermes uses `hermes-agent / contributor`. It must never review, approve,
promote, merge, or claim that it has completed a Wiki write. `稍后` defaults to
seven days. `忽略` rejects the candidate while retaining the audit record.

## 3. What 0.5.3 Changed

The implementation and automated acceptance are complete. Real-host Hook
observation is in progress.

- Skill guidance now uses quiet capture, explicit intent, and a one-prompt
  limit.
- MCP result payloads expose `candidate_path`, `status`, `target`,
  `operation`, `next_action`, `next_required_role`, `snoozed_until`, and
  `blocker_code` where applicable.
- `contributor` completion explicitly reports the Inbox handoff; `compiler`
  completion explicitly reports the final Wiki result.
- Title, value reason, and body are scanned before propose, approve, promote,
  and merge. High-confidence secret patterns are blocked before persistence.
- A missing or invalid suggested Wiki target is rejected during proposal,
  rather than silently changing destination later.
- `snooze` without a supplied date resolves to seven days.

Local verification already passed:

```powershell
python -m py_compile src\agentskm_toolkit\km.py src\agentskm_toolkit\mcp.py tests\acceptance\test_km_workflow.py
python scripts\check_versions.py
python scripts\build_plugin.py --check
python scripts\check_repo_purity.py
python tests\acceptance\test_km_workflow.py
```

Codex has also completed an explicit compiler capture and Wiki promotion. This
proves the explicit-intent execution path, not reliable passive detection.

## 4. Why Hermes Hooks Matter

The AgentsKM Skill can semantically recognize a verified reusable outcome, but
it is model-routed guidance. It cannot guarantee that the host evaluates every
completed task when the user did not mention AgentsKM.

Hermes provides host-level Hook systems. Relevant events are:

| Event | Use in this pilot | Do not use it as |
| --- | --- | --- |
| `pre_verify` | Best first test for code-edit tasks immediately before completion | A general conversation event |
| `agent:end` (Gateway Hook) | Best per-incoming-message completion event in Gateway mode | Automatic authorization to write knowledge |
| `on_session_end` | Final fallback extraction on exit, reset, or expiry | A per-turn completion event |
| `on_session_finalize` | Final session cleanup/fallback | A replacement for the normal prompt flow |
| `post_llm_call` | Diagnostics only | A capture trigger; it fires too often and may occur before task completion |

The target architecture is:

```text
Hermes event
  -> non-writing capture assessment
     -> candidate gate: reusable + verified + safe + non-duplicate
        -> one user-visible prompt in the normal conversation
           -> existing contributor MCP flow
              -> 000_Inbox and reviewer/compiler handoff
```

A Hook must not directly create a Wiki page, silently write Inbox content, or
grant permanent authorization. It provides timing and observability; the Skill
and MCP continue to decide content and enforce permissions.

## 5. Hermes Environment Preconditions

The previously observed editable-install launcher failure is resolved on the
environment that completed the real `0.5.3` capture. On a new machine, verify
the launchers before testing AgentsKM integration.

After repair, verify the host before editing any AgentsKM configuration:

```powershell
hermes --help
hermes-agent --help
uvx --version
```

For the released runtime, configure `--from agentskm-toolkit==0.5.3`. For an
unreleased local pilot, change only the `--from` value to the resolved local
wheel path while preserving:

```text
agentskm mcp --profile hermes-agent --host hermes --bootstrap-role contributor
```

Example shape, with `<repo-root>` replaced locally and never committed:

```yaml
mcpServers:
  agentskm:
    command: uvx
    args:
      - --from
      - <repo-root>/dist/agentskm_toolkit-0.5.3-py3-none-any.whl
      - agentskm
      - mcp
      - --profile
      - hermes-agent
      - --host
      - hermes
      - --bootstrap-role
      - contributor
```

Fully restart Hermes after changing the package source or role. If its MCP
schema cache still describes an older interface, refresh only the AgentsKM
entry after the runtime is healthy. Do not delete user Vault data or unrelated
Hermes state.

## 6. Pilot Phase A: Prove Hook Delivery Without Writes

Start with a harmless Hook that writes only timestamp, event name, session ID,
and bounded metadata to a local pilot log outside the Toolkit repository. Do
not log full conversation text, model requests, secrets, or MCP payloads.

Test one event at a time:

1. Register `pre_verify` for a small code-edit task. Confirm one log event is
   emitted only when Hermes is about to finish a task that edited files.
2. If using Hermes Gateway, register `agent:end`. Confirm it emits once when a
   user message has been fully processed.
3. Reset or end a session and confirm `on_session_end` fires once as a fallback.
4. Do not use `post_llm_call` for capture decisions; use it only to understand
   invocation frequency if required.

Success criteria:

- Hook errors do not block normal work.
- Events have stable enough session/task identifiers for deduplication.
- No full transcript or secret enters the pilot log.
- Repeated retries do not produce duplicate event records for the same unit of
  work.

## 7. Pilot Phase B: Verify the MCP Contributor Boundary

Before testing passive capture, open a fresh Hermes session and send this
read-only prompt:

```text
请只使用当前配置的 AgentsKM MCP，不要读取 Toolkit 本地源码，也不要运行裸 agentskm CLI。

1. 调用 km_doctor，报告 Toolkit version、Profile、Role、Config path、Vault path、State 和 Next action。
2. 列出当前可见的 AgentsKM MCP tools。
3. 调用 km_status 和 km_validate，但不要写入 Inbox 或 Wiki。
4. 判断当前 Profile 是否只能执行 contributor 权限。
```

Expected result:

```text
Toolkit version: 0.5.3
Profile: hermes-agent
Role: contributor
State: ready
```

Visible tools must include `km_propose_capture` and `km_respond_candidate`.
They must exclude `km_review_candidate`, `km_dashboard`,
`km_promote_candidate`, and `km_merge_candidate`.

Then run one controlled Inbox test:

```text
请使用 km_propose_capture 创建一条真实 Inbox 候选，dry_run=false：
- title: AgentsKM Hermes 0.5.3 Hook 验收
- type: note
- value_reason: 验证 Hermes contributor 只能将候选提交到公共 Inbox，不能直接写入 Wiki
- body: Hermes Hook 应只在合适时机触发知识评估；通过候选门槛后，Hermes contributor 提交 Inbox，等待 reviewer 或 compiler 审核。
- source_session: hermes-0.5.3-hook-acceptance
- agent_id: hermes-agent
- source_tool: hermes-mcp

完成后报告 candidate_id、状态、candidate_path 和 next_required_role。不要尝试审核、晋升或合并。
```

Use a Codex `compiler` session to inspect or process that candidate afterward.
That validates the shared Vault and preserves separation of duties.

## 8. Pilot Phase C: Passive-Capture Experiment

Only after Phase A and B pass:

1. Have Hermes complete a real, bounded technical task with a verifiable
   result. Do not mention AgentsKM, `沉淀`, or `记住这条`.
2. Let the selected Hook provide a compact event signal to the capture
   assessment path. It must not persist content itself.
3. The assessment must decide no more than one of these outcomes:
   - no action for trivial, uncertain, duplicate, or sensitive material;
   - a single normal-conversation prompt for a qualified candidate;
   - a diagnostic record that the assessment was skipped or blocked.
4. If the user chooses `沉淀`, Hermes records contributor capture intent and
   reports the Inbox path and required next role.
5. Repeat with a trivial task and with secret-like input. Neither should create
   a candidate or prompt.

Record only aggregate pilot metrics:

- qualified prompt count per technical conversation;
- accept, snooze, and ignore rates;
- false positives and missed high-value outcomes;
- duplicate rate;
- time from Inbox to compiler review;
- interruption quality as reported by the user.

## 9. Guardrails And Non-Goals

- Never edit Vault Markdown directly; use AgentsKM MCP.
- Never include config files, Vault files, credentials, tokens, conversation
  transcripts, or local absolute paths in commits or issue text.
- Never use a Hook to bypass missing MCP tools, role boundaries, candidate
  states, review, or safety checks.
- Do not automatically resolve conflicting Wiki claims or overwrite an existing
  page.
- Do not treat session-end extraction as authorization to persist a full
  transcript.
- Do not add a database, vector store, or generic autonomous workflow during
  this pilot. Establish signal quality first.

## 10. Decision Points After the Pilot

- If `pre_verify` produces useful, low-interruption signals, retain it for
  coding tasks and keep `on_session_end` only as a fallback.
- If Gateway `agent:end` works reliably, create a Gateway-specific adapter;
  do not claim it works for CLI/Desktop without a separate test.
- If prompts are frequently ignored, tighten the candidate gate before adding
  more automation.
- If high-value tasks are repeatedly missed, improve the assessment contract or
  add a host-specific adapter. Do not weaken safety or role enforcement.
- Keep the stable Hermes package pin on the exact production PyPI version that
  passed the release workflow and host smoke test.

## 11. Pilot Findings And Host Policy

The first Hermes `0.5.3` pilot completed the explicit contributor flow and
confirmed that the implicit-capture Hook can run. The main usability failure
was target-path discoverability: three invalid proposals were attempted before
the canonical `wiki/concepts/project-state-space.md` shape was discovered.
The runtime and MCP contract now return the accepted format, an example, and an
actionable `next_action` for this error.

The current host policy is deliberately asymmetric:

- Desktop environments without a reliable lifecycle Hook use explicit user
  requests such as `沉淀` or `记住这条`.
- Hermes CLI may automatically run the non-writing capture assessment through
  its Hook. Persistence still requires the normal permission-aware flow.
- A Hermes contributor capture ends in Inbox and reports the next required
  reviewer/compiler role; it never reports Wiki completion.

The persisted Inbox status remains `reminded` for compatibility after a
contributor records `capture`. Host-facing responses should present
`intent_status: capture_requested` and `next_action: await_review` instead of
describing the result as merely reminded.

## 12. Relevant Repository References

- `docs/architecture.md`: product boundaries and role model.
- `docs/agent-knowledge-protocol.md`: candidate schema and state transitions.
- `docs/permission-aware-capture-plan.md`: design decisions and completed
  implementation work.
- `docs/guides/mcp-hosts.md`: host MCP acceptance flow.
- `integrations/hermes/README.md`: minimal Hermes MCP registration template.
- `docs/release-checklist.md`: TestPyPI/PyPI release procedure.
