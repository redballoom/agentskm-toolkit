# Acceptance Tests

The suite copies the source Vault into a temporary directory and performs real
writes there. The live Vault and user configuration are not modified.

```powershell
python tests/acceptance/test_km_workflow.py
```

When the repository itself is not a Vault, set `AGENTSKM_DATA_ROOT` only as a
test-fixture source override. Runtime configuration under test uses a temporary
`AGENTSKM_CONFIG` and Profile model.

Coverage includes Bootstrap-only MCP tools, idempotent Setup, explicit
Compiler confirmation, legacy config migration and backup, search priority,
role rejection, reminders, review, snooze, promotion, merge, duplicate
candidate contribution merging, dashboard generation, qmd readiness, HTTP
authentication, Profile-based MCP exposure, second-Agent configuration
generation, Skill Setup guidance, and self-contained plugin packaging.
