# AgentsKM Operations Runbook

> 日期：2026-07-27

## 1. 安装与 Setup

终端用户安装插件或 MCP 包，不需要克隆 Toolkit。首次启动 MCP 时自动生成：

```text
配置：%USERPROFILE%\.agentskm\config.json
Vault：%USERPROFILE%\Documents\AgentsKM\vault
Codex：codex / compiler
Hermes、Claude、Cursor：各自 Profile / contributor
```

默认 Vault 是带 README、Inbox、Wiki、Raw 和 docs 目录的空知识库。已有知识
库可以通过 Git 克隆或备份恢复，然后把 `vaults.main.path` 改成其绝对路径。
CLI 每次调用都从配置文件重新解析 Vault 和角色，因此改路径无需重启。

Codex Compiler Profile 需要显式确认：

```powershell
python tools\km-cli\km.py setup `
  --profile codex --host codex --role compiler `
  --vault-name main --confirm-compiler
```

Vault、Profile 与角色只以配置文件和 MCP 显式 Profile 参数为准，不使用环境变量。

快速诊断与升级：

```powershell
python tools\km-cli\km.py doctor --profile codex
python tools\km-cli\km.py update
```

升级会从 GitHub Git marketplace 或源码仓库获取最新版。升级后重新连接 MCP；
不在写入中途终止 Agent 进程。Codex 中新建会话是可靠的冷重载边界。

## 2. 日常查询

```powershell
python tools\km-cli\km.py search "领星 API 鉴权"
python tools\km-cli\km.py pending
python tools\km-cli\km.py reminders
```

查询优先返回 Wiki。Inbox 必须标记为未审核，Raw 只作为证据。

## 3. 对话捕获

Agent 在回答前发现可复用结论时：

```powershell
python tools\km-cli\km.py propose `
  --title "候选标题" `
  --value-reason "这条结论可跨项目复用" `
  --source-ref "conversation:task-id" `
  --suggested-target "wiki/concepts/example.md" `
  --agent-id codex `
  --source-tool codex-mcp `
  --source-session task-id

python tools\km-cli\km.py review 000_Inbox/example.md `
  --decision remind
```

然后询问用户：`沉淀 / 稍后 / 忽略`。

## 4. 用户决定

沉淀：

```powershell
python tools\km-cli\km.py review 000_Inbox/example.md `
  --decision approve --reviewed-by user

python tools\km-cli\km.py promote 000_Inbox/example.md `
  --approved-by user `
  --scope "用户批准该候选毕业"
```

目标已有页面时改用 `km merge --target <existing-wiki-page>`。

稍后：

```powershell
python tools\km-cli\km.py review 000_Inbox/example.md `
  --decision snooze --until 2026-08-03 `
  --reviewed-by user
```

忽略：

```powershell
python tools\km-cli\km.py review 000_Inbox/example.md `
  --decision reject --reviewed-by user
```

Inbox 审计记录不删除。

Inbox 为所有 Agent 共用。候选开头的 `agent_id`、`source_tool`、
`source_session`、`source_refs` 标明来源；重复主题合并贡献 Agent 和会话来源。

## 5. 多 Agent

- Codex 插件：自包含 Skill、CLI 和 compiler MCP。
- Claude Code/Cursor：使用 `scripts/render_mcp_config.py` 生成 contributor 配置。
- 只有明确需要执行审批结果的可信宿主才配置 compiler。
- 拥有不受限 Shell 的 Agent 仍属于操作系统信任边界；MCP 角色不能替代系统权限隔离。

## 6. HTTP

```powershell
python adapters\http\km_http.py --host 127.0.0.1 --port 8765 --profile hermes-agent --token local-secret
```

所有 POST 请求必须携带 `Authorization: Bearer <token>`。不要监听公网地址。

## 7. 验收

```powershell
python scripts\build_plugin.py --check
python tools\km-cli\km.py validate
python tools\km-cli\km.py lint
python tests\acceptance\test_km_workflow.py
```

验收测试只在临时 Vault 中执行写入。
