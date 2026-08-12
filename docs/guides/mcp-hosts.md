# Hermes、Claude、Cursor 与通用 MCP 指南

不同 Agent 没有统一插件协议，但只要支持 stdio MCP，就可以使用同一个 AgentsKM
PyPI runtime。最终用户不需要克隆 Toolkit，也不需要全局安装 `agentskm`。

## 1. 前置条件

在启动 Agent 的同一环境中确认：

```powershell
uvx --version
uvx --isolated --no-cache --from agentskm-toolkit==0.5.3 agentskm --version
```

第二条命令预期输出 `0.5.3`。如果终端能找到 `uvx` 而桌面 Agent 找不到，应完全退出
并重启 Agent，使其重新读取 `PATH`。

## 2. MCP 配置模板

Hermes：

```json
{
  "mcpServers": {
    "agentskm": {
      "command": "uvx",
      "args": [
        "--from", "agentskm-toolkit==0.5.3",
        "agentskm", "mcp",
        "--profile", "hermes-agent",
        "--host", "hermes",
        "--bootstrap-role", "contributor"
      ]
    }
  }
}
```

Claude：

```json
{
  "mcpServers": {
    "agentskm": {
      "command": "uvx",
      "args": [
        "--from", "agentskm-toolkit==0.5.3",
        "agentskm", "mcp",
        "--profile", "claude",
        "--host", "claude",
        "--bootstrap-role", "contributor"
      ]
    }
  }
}
```

Cursor 项目配置写入 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "agentskm": {
      "command": "uvx",
      "args": [
        "--from", "agentskm-toolkit==0.5.3",
        "agentskm", "mcp",
        "--profile", "cursor",
        "--host", "cursor",
        "--bootstrap-role", "contributor"
      ]
    }
  }
}
```

其他宿主将 `profile` 和 `host` 改为稳定、唯一的名称即可。不要让多个宿主共用同一个
`actor_id`；需要新增或调整 Profile 时使用 CLI 的显式 Setup 流程。

## 3. 首次启动发生什么

Agent 启动 MCP 后，`uvx` 下载并隔离运行固定版本。AgentsKM 随后：

1. 读取 `~/.agentskm/config.json`。
2. 配置缺失时创建 `main` Vault 和当前 contributor Profile。
3. Profile 缺失时将其接入已有 `main` Vault。
4. 启动后按 Profile 角色固定本次连接的工具列表。

如果已有同名 Profile，但 host、角色、actor 或 Vault 不一致，Setup 会失败并报告冲突，
不会覆盖现有身份。

## 4. Hermes 验收提示词

先做只读检查：

```text
请只使用当前配置的 AgentsKM MCP，不要读取 Toolkit 本地源码，不要运行裸 agentskm CLI。

1. 调用 km_doctor，报告 Toolkit version、Profile、Role、Config path、Vault path、State 和 Next action。
2. 列出当前可见的 AgentsKM MCP tools。
3. 调用 km_status 和 km_validate，但不要写入 Inbox 或 Wiki。
4. 判断当前 Profile 是否只能执行 contributor 权限。
```

Hermes 默认预期为 `hermes-agent / contributor / ready`。可见工具应包含：

```text
km_setup_status, km_doctor, km_update, km_status, km_pending,
km_reminders, km_search, km_validate, km_lint,
km_respond_candidate, km_propose_capture
```

不应暴露 `km_review_candidate`、`km_dashboard`、`km_promote_candidate` 或
`km_merge_candidate`。

## 5. 真实 Inbox 写入验收

确认只读验收通过后发送：

```text
请使用 km_propose_capture 创建一条真实 Inbox 候选，dry_run=false：
- title: AgentsKM Hermes 0.5.3 验收
- type: note
- value_reason: 验证 Hermes contributor 可以向公共 Inbox 提交候选，但不能直接写入 Wiki
- body: Hermes 作为 contributor，应能提出知识沉淀候选，并由 reviewer/compiler 后续审核、晋升或合并。
- source_session: hermes-0.5.3-acceptance
- agent_id: hermes-agent
- source_tool: hermes-mcp

完成后报告 candidate_id、状态和来源字段。再次列出工具，确认 promote/merge 不可见；不要绕过角色边界。
```

随后在 Codex compiler 会话中搜索该 `candidate_id`，检查来源，完成 review，再按用户意图
promote 或 merge。这一步验证多个 Agent 确实连接到同一个 Vault。

## 6. 日常交互规则

建议为宿主增加以下项目规则：

```text
涉及可复用经验时，先搜索 AgentsKM Wiki；Inbox 结果必须标记为未审核。
对话产生已验证的方案、排障路径、架构决策或 SOP 时，先查重，再提交至公共 Inbox。
创建候选后告诉用户标题和价值，并询问：沉淀 / 稍后 / 忽略。
只通过 AgentsKM MCP 写入，不直接编辑 Vault Markdown。
contributor 不审核、不晋升、不合并 Wiki。
```

## 7. 共享现有 Vault

同一台电脑上的所有 Profile 默认读取同一个用户配置。若 Codex 已配置
`vaults.main.path`，新 Hermes/Claude/Cursor Profile 会接入该 `main` Vault。

迁移到其他电脑时，先把用户选择的 Vault 放到目标位置，再通过 CLI Setup 指定路径：

```powershell
uvx --from agentskm-toolkit==0.5.3 agentskm setup `
  --profile hermes-agent --host hermes --role contributor `
  --vault-name main --vault "D:\Knowledge\AgentsKM\vault"
```

完成后重启宿主或重新连接 MCP。

## 8. 更新

其他 Agent 的版本由 MCP 配置中的 PyPI pin 决定。发布新版本后：

1. 将 `agentskm-toolkit==0.5.3` 改为已验收的新版本。
2. 完全重连 MCP 或开启新会话。
3. 调用 `km_doctor` 确认实际加载版本。
4. 重新检查 contributor 工具边界。

不要使用浮动的未固定版本作为生产配置，以免不同 Agent 在同一时间运行不同契约。

