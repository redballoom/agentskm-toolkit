# KM CLI

Minimal local CLI for AgentsKM.

By default the CLI treats the repository containing `tools/km-cli/km.py` as the
knowledge root. For split installs, bind it to a separate vault with:

```powershell
$env:AGENTSKM_DATA_ROOT="D:\Human-Agent_Collab\AGENTSKM\agentskm-vault"
python tools/km-cli/km.py status
```

Read commands:

```powershell
python tools/km-cli/km.py status
python tools/km-cli/km.py pending
python tools/km-cli/km.py search "领星 API 鉴权"
python tools/km-cli/km.py validate
python tools/km-cli/km.py lint
python tools/km-cli/km.py dashboard
python tools/km-cli/km.py qmd-readiness
```

Add `--json` to any command when an adapter or Agent needs structured output:

```powershell
python tools/km-cli/km.py status --json
python tools/km-cli/km.py search "领星 API 鉴权" --limit 1 --json
```

Write commands:

```powershell
python tools/km-cli/km.py propose --title "候选标题" --type concept --tags "api,auth" --source-ref raw/articles/example.md --suggested-target wiki/concepts/example.md --value-reason "可复用"
python tools/km-cli/km.py promote 000_Inbox/example.md --target wiki/concepts/example.md --approved-by user --scope "用户明确批准"
```

Write commands use a repository lock under `.km/locks/`, atomic file replacement, rollback-on-failure backups, and transaction records under `.km/transactions/`.
`promote` refuses candidates that are already terminal, have `sensitivity: secret`, or lack `source_refs`.

HTTP adapters should call this CLI with `--json`; they must not duplicate validation or promotion rules.

Obsidian review dashboard:

```powershell
python tools/km-cli/km.py dashboard --output docs/review-dashboard.md
```

Open `docs/review-dashboard.md` in Obsidian to review pending Inbox candidates and formal Wiki pages.

QMD readiness report:

```powershell
python tools/km-cli/km.py qmd-readiness --output docs/qmd-readiness.md
```

Use this report to decide whether to keep deferring qmd or start evaluating it.
