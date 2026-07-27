# Acceptance Tests

The suite copies the configured Vault into a temporary directory and performs
real writes there. The live Vault is not modified.

```powershell
$env:AGENTSKM_DATA_ROOT="D:\path\to\agentskm-vault"
python tests/acceptance/test_km_workflow.py
```

Coverage includes search priority, configure, role rejection, reminders,
snooze, approval, promotion, merge, duplicate contributor aggregation, HTTP
authentication, contributor/compiler MCP profiles, a generated Claude MCP
configuration, and the self-contained plugin runtime.
