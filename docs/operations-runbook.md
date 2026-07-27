# AgentsKM Operations Runbook

> 日期：2026-07-27

## 1. 安装与 Setup

终端用户安装插件或 MCP 包，不需要克隆 Toolkit。已有知识库可以通过 Git
克隆、备份恢复或已有本地目录准备。首次为 Hermes 配置：

```powershell
python tools\km-cli\km.py setup-status --profile hermes-agent

python tools\km-cli\km.py setup `
  --profile hermes-agent `
  --host hermes `
  --role contributor `
  --vault-name main `
  --vault D:\path\to\agentskm-vault
```

配置保存到 `%USERPROFILE%\.agentskm\config.json`。MCP 缺少配置时只暴露
`km_setup_status` 和 `km_setup_instructions`。Setup 完成后重启 Agent 或重新
连接 MCP。

Codex Compiler Profile 需要显式确认：

```powershell
python tools\km-cli\km.py setup `
  --profile codex --host codex --role compiler `
  --vault-name main --confirm-compiler
```

日常只使用 `AGENTSKM_CONFIG` 和 `AGENTSKM_PROFILE`。旧环境变量和角色参数
仅用于过渡兼容。

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
  --actor-role contributor

python tools\km-cli\km.py review 000_Inbox/example.md `
  --decision remind `
  --actor-role reviewer
```

然后询问用户：`沉淀 / 稍后 / 忽略`。

## 4. 用户决定

沉淀：

```powershell
python tools\km-cli\km.py review 000_Inbox/example.md `
  --decision approve --reviewed-by user --actor-role reviewer

python tools\km-cli\km.py promote 000_Inbox/example.md `
  --approved-by user `
  --scope "用户批准该候选毕业" `
  --actor-role compiler
```

目标已有页面时改用 `km merge --target <existing-wiki-page>`。

稍后：

```powershell
python tools\km-cli\km.py review 000_Inbox/example.md `
  --decision snooze --until 2026-08-03 `
  --reviewed-by user --actor-role reviewer
```

忽略：

```powershell
python tools\km-cli\km.py review 000_Inbox/example.md `
  --decision reject --reviewed-by user --actor-role reviewer
```

Inbox 审计记录不删除。

## 5. 多 Agent

- Codex 插件：自包含 Skill、CLI 和 compiler MCP。
- Claude Code/Cursor：使用 `scripts/render_mcp_config.py` 生成 contributor 配置。
- 只有明确需要执行审批结果的可信宿主才配置 compiler。
- 拥有不受限 Shell 的 Agent 仍属于操作系统信任边界；MCP 角色不能替代系统权限隔离。

## 6. HTTP

```powershell
$env:AGENTSKM_HTTP_TOKEN="local-secret"
python adapters\http\km_http.py --host 127.0.0.1 --port 8765 --role contributor
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
