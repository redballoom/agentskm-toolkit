# CLI Compatibility Launcher

`km.py` is retained only for old source-checkout integrations. It imports the
packaged CLI from `src/agentskm_toolkit` and contains no business logic.

Use the supported entrypoint instead:

```powershell
agentskm --help
agentskm doctor --profile codex
agentskm search "topic" --profile codex
```

For install-on-use hosts:

```powershell
uvx --from agentskm-toolkit==0.5.0 agentskm --help
```

The CLI remains the only implementation for config, Profile roles, Vault
paths, locking, transactions, audit history, Inbox writes, review, promote,
and merge operations.
