# AgentsKM CLI 用户指南

CLI 是配置、权限、Vault、锁、事务、审计、Inbox 和 Wiki 操作的唯一业务实现。MCP
最终也调用这套 CLI 逻辑。普通 Agent 对话优先使用 MCP；终端适合 Setup、恢复诊断、
自动化和人工审核。

## 1. 运行方式

无需持久安装：

```powershell
uvx --from agentskm-toolkit==0.5.2 agentskm --version
uvx --from agentskm-toolkit==0.5.2 agentskm --help
```

需要经常在终端操作时，可以安装为 `uv` tool：

```powershell
uv tool install agentskm-toolkit==0.5.2
agentskm --version
```

以下示例使用持久安装后的 `agentskm`。使用 `uvx` 时，只需在命令前替换为：

```text
uvx --from agentskm-toolkit==0.5.2 agentskm
```

## 2. Setup

创建 contributor Profile：

```powershell
agentskm setup --profile hermes-agent --host hermes --role contributor
```

创建专用 reviewer Profile：

```powershell
agentskm setup --profile km-reviewer --host reviewer --role reviewer
```

创建 compiler Profile 必须显式确认：

```powershell
agentskm setup --profile codex --host codex --role compiler --confirm-compiler
```

指定已有 Vault：

```powershell
agentskm setup --profile codex --host codex --role compiler `
  --confirm-compiler --vault-name main --vault "D:\Knowledge\AgentsKM\vault"
```

先预览而不写入：

```powershell
agentskm setup --profile codex --host codex --role compiler `
  --confirm-compiler --vault "D:\Knowledge\AgentsKM\vault" --dry-run --json
```

Setup 是幂等操作；相同配置可重复执行，冲突配置会失败关闭。配置变化后应重连所有受
影响的 MCP 会话。

## 3. 健康检查

```powershell
agentskm setup-status --profile codex --json
agentskm doctor --profile codex --json
agentskm status --profile codex --json
agentskm validate --profile codex --json
agentskm lint --profile codex --json
```

`doctor` 返回 `state: ready` 和 `next_action: ready` 才表示配置、Vault、写权限和锁状态
正常。退出码含义：

```text
0: 成功
1: 检查完成，但发现健康或校验问题
2: 输入、配置、路径、权限或运行错误
```

## 4. 搜索和提醒

```powershell
agentskm search "MCP 权限" --profile hermes-agent --json
agentskm pending --profile hermes-agent --json
agentskm reminders --profile hermes-agent --json
```

Wiki 命中可作为已审核知识使用；Inbox 命中必须标记为未审核候选。

## 5. contributor 提交候选

先使用 `--dry-run` 检查：

```powershell
agentskm propose --profile hermes-agent --dry-run --json `
  --title "MCP 角色工具可见性" `
  --type note `
  --value-reason "记录 contributor 与 compiler 的工具边界" `
  --body "MCP 应按连接时的 Profile 角色暴露固定工具列表。" `
  --source-session "manual-cli-test" `
  --agent-id "hermes-agent" `
  --source-tool "agentskm-cli"
```

确认后移除 `--dry-run` 创建候选。不得把 Token、密码、客户数据、个人数据或未经验证
的判断写入候选。

contributor 根据用户选择记录意向：

```powershell
agentskm respond <candidate-id> --profile hermes-agent `
  --decision capture --responded-by "user" --reason "用户同意沉淀"
```

其他决定可使用 `snooze`、`reject` 或 `remind`。`snooze` 时通过 `--until` 指定日期。

## 6. reviewer 审核

```powershell
agentskm review <candidate-id> --profile km-reviewer `
  --decision approve --reviewed-by "reviewer-id" --reason "内容已验证且无敏感信息"
```

reviewer 也可以选择 `snooze`、`reject` 或 `remind`，并可生成审核面板：

```powershell
agentskm dashboard --profile km-reviewer
```

用户的“沉淀”意向不等于质量审核通过；两项状态应分别保留。
个人工作流可以由 compiler 使用其内含的 reviewer 能力完成审核；需要职责分离时，再使用
独立 reviewer Profile 和身份。

## 7. compiler 晋升或合并

新建 Wiki 页面：

```powershell
agentskm promote <candidate-id> --profile codex `
  --approved-by "user" --scope "将本候选创建为独立 Wiki 页面" `
  --target "wiki/concepts/mcp-role-visibility"
```

合并到已有 Wiki 页面：

```powershell
agentskm merge <candidate-id> --profile codex `
  --approved-by "user" --scope "合并到既有 MCP 权限文档" `
  --target "wiki/concepts/agentskm-permissions.md"
```

候选必须已获审核批准并具有明确用户授权。`--approved-by` 和 `--scope` 是审计信息，
不能用虚构值绕过流程。

## 8. 更新和恢复

检查当前进程给出的更新建议：

```powershell
agentskm update --check --json
```

持久安装升级时，将版本替换为已发布并验收的版本：

```powershell
uv tool install --force agentskm-toolkit==<version>
agentskm --version
```

`uvx` 用户直接更新命令中的版本 pin。更新后重新运行 `doctor`，并重连使用该 runtime
的 MCP 宿主。

不要通过删除 `~/.agentskm/config.json` 或 Vault 来修复插件安装问题。先运行 doctor，
根据 `next_action` 处理；Vault 数据与程序安装生命周期相互独立。
