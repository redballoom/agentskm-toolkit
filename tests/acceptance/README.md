# Acceptance Tests

Run:

```powershell
python tests/acceptance/test_km_workflow.py
```

The acceptance workflow verifies:

- CLI status/search/pending JSON output.
- Search for `领星 API 鉴权` resolves to the formal Wiki page.
- `propose --dry-run` does not create a candidate file.
- `promote` refuses a candidate without `source_refs`.
- HTTP adapter GET/POST paths.
- MCP `initialize`, `tools/list`, `km_search`, and `km_promote_candidate` guardrail.

