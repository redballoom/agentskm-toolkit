# KM CLI

Deterministic local core for AgentsKM. It is the only supported Markdown
write path for Agents and adapters.

## Setup

```powershell
python tools/km-cli/km.py setup-status --profile hermes-agent

python tools/km-cli/km.py setup `
  --profile hermes-agent `
  --host hermes `
  --role contributor `
  --vault-name main
```

Setup writes `%USERPROFILE%\.agentskm\config.json`. When no Vault is supplied,
it creates `%USERPROFILE%\Documents\AgentsKM\vault` with an empty Inbox, Wiki
layers, index, and usage instructions. Repeating the same command is a no-op.
Creating a compiler Profile additionally requires `--confirm-compiler`.

The config file is the sole runtime source for Vault paths and roles. MCP
servers pass the Profile explicitly. Environment variables are not used for
config, Profile, role, or Vault selection. `--config` is reserved for isolated
diagnostics and tests; `--actor-role` remains a deprecated compatibility flag.

## Diagnose And Update

```powershell
python tools/km-cli/km.py doctor --profile codex
python tools/km-cli/km.py update
```

`update` fast-forwards a source checkout or refreshes and reinstalls a Codex
Git marketplace package. A code update requires a new conversation or MCP
reconnect; Setup and config path changes do not.

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
  --suggested-target "wiki/concepts/example.md"

python tools/km-cli/km.py respond 000_Inbox/example.md `
  --decision capture `
  --responded-by user

python tools/km-cli/km.py review 000_Inbox/example.md `
  --decision remind

python tools/km-cli/km.py respond 000_Inbox/example.md `
  --decision capture `
  --responded-by user

python tools/km-cli/km.py review 000_Inbox/example.md `
  --decision snooze `
  --until 2026-08-03 `
  --reviewed-by user

python tools/km-cli/km.py respond 000_Inbox/example.md `
  --decision capture `
  --responded-by user

python tools/km-cli/km.py review 000_Inbox/example.md `
  --decision approve `
  --reviewed-by user
```

## Compile Approved Knowledge

```powershell
python tools/km-cli/km.py promote 000_Inbox/example.md `
  --target wiki/concepts/example.md `
  --approved-by user `
  --scope "用户批准该候选毕业"

python tools/km-cli/km.py merge 000_Inbox/example.md `
  --target wiki/concepts/existing.md `
  --approved-by user `
  --scope "用户批准合并到已有页面"
```

Roles are enforced by CLI commands. MCP profiles also hide tools above their
configured role. This is a workflow boundary, not an operating-system sandbox
against Agents that already have unrestricted shell access.

Write commands use a repository lock, atomic replacement, rollback backups,
and transaction records under `.km/`.
