# Acceptance Tests

The suite creates a self-contained fixture Vault in a temporary directory and
performs real writes there. The live Vault and user configuration are not
modified.

```powershell
python tests/acceptance/test_km_workflow.py
```

Set `AGENTSKM_DATA_ROOT` only when intentionally overriding the built-in test
fixture with another Vault. Runtime configuration under test always uses a
temporary config file and Profile model.

Coverage includes Bootstrap-only MCP tools, idempotent Setup, explicit
Compiler confirmation, legacy config migration and backup, search priority,
role rejection and override prevention, path boundaries, Frontmatter escaping,
secret rejection, reminders, review, snooze, promotion, merge, duplicate
candidate contribution merging, dashboard generation, qmd readiness, HTTP
authentication, Profile-based MCP exposure, second-Agent configuration
generation, Skill Setup guidance, and lightweight PyPI-backed plugin packaging.
