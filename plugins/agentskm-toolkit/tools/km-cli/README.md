# KM CLI

Deterministic local core for AgentsKM. It is the only supported Markdown
write path for Agents and adapters.

## Bind A Vault

```powershell
python tools/km-cli/km.py configure --vault D:\path\to\agentskm-vault
```

The binding is stored at `%USERPROFILE%\.agentskm\config.json`. An explicit
`AGENTSKM_DATA_ROOT` environment variable takes precedence.

## Read

```powershell
python tools/km-cli/km.py status
python tools/km-cli/km.py search "领星 API 鉴权"
python tools/km-cli/km.py pending
python tools/km-cli/km.py reminders
python tools/km-cli/km.py validate
python tools/km-cli/km.py lint
```

Add `--json` for Agent or adapter calls.

## Capture And Review

```powershell
python tools/km-cli/km.py propose `
  --title "候选标题" `
  --value-reason "可跨项目复用" `
  --source-ref "conversation:task-id" `
  --suggested-target "wiki/concepts/example.md" `
  --actor-role contributor

python tools/km-cli/km.py review 000_Inbox/example.md `
  --decision remind `
  --actor-role reviewer

python tools/km-cli/km.py review 000_Inbox/example.md `
  --decision snooze `
  --until 2026-08-03 `
  --reviewed-by user `
  --actor-role reviewer

python tools/km-cli/km.py review 000_Inbox/example.md `
  --decision approve `
  --reviewed-by user `
  --actor-role reviewer
```

## Compile Approved Knowledge

```powershell
python tools/km-cli/km.py promote 000_Inbox/example.md `
  --target wiki/concepts/example.md `
  --approved-by user `
  --scope "用户批准该候选毕业" `
  --actor-role compiler

python tools/km-cli/km.py merge 000_Inbox/example.md `
  --target wiki/concepts/existing.md `
  --approved-by user `
  --scope "用户批准合并到已有页面" `
  --actor-role compiler
```

Roles are enforced by CLI commands. MCP profiles also hide tools above their
configured role. This is a workflow boundary, not an operating-system sandbox
against Agents that already have unrestricted shell access.

Write commands use a repository lock, atomic replacement, rollback backups,
and transaction records under `.km/`.
