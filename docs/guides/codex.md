# Codex 插件用户指南

Codex 用户通过官方 GitHub Marketplace 安装轻量插件。插件提供 AgentsKM Skill、
Codex 命令描述和 MCP 注册；真正的 CLI/MCP runtime 由 `uvx` 从 PyPI 获取固定版本
`agentskm-toolkit==0.5.3`。

## 1. 安装前检查

在新终端运行：

```powershell
uvx --version
codex plugin --help
```

如果 `uvx` 不存在，先安装 Astral `uv` 并重新打开终端，确保 Codex 启动时继承到
更新后的 `PATH`。

## 2. 全新安装

Marketplace 清单位于仓库根目录，因此不要传 `--sparse`：

```powershell
codex plugin marketplace add redballoom/agentskm-toolkit --ref main
codex plugin add agentskm-toolkit@agentskm-official
```

预期安装来源名称为 `agentskm-official`，插件版本为 `0.5.3`。安装完成后开启一个新
Codex 会话，让宿主启动新 MCP 连接。

## 3. 首次只读验收

在新会话中发送：

```text
请只使用 agentskm-toolkit@agentskm-official 暴露的 AgentsKM MCP，不要读取本地源码，也不要运行裸 agentskm CLI。

1. 调用 km_doctor，报告 Toolkit version、Profile、Role、Config path、Vault path、State 和 Next action。
2. 列出当前可见的 AgentsKM MCP tools。
3. 调用 km_status，报告 Inbox 和 Wiki 数量；不要创建或修改任何候选。
```

默认预期：

```text
Toolkit version: 0.5.3
Profile: codex
Role: compiler
State: ready
Next action: ready
```

compiler 应能看到 contributor 的基础工具以及：

```text
km_review_candidate
km_dashboard
km_promote_candidate
km_merge_candidate
```

## 4. 日常使用

无需记忆工具名，可以直接提出意图：

```text
先在 AgentsKM Wiki 中搜索我们以前是否记录过这个问题，再继续分析。
```

```text
检查这次对话是否产生了已验证、可复用的知识。如果有，先查重，再告诉我标题、价值和建议目标，并让我选择：沉淀 / 稍后 / 忽略。
```

```text
列出当前待审核候选，说明来源、状态和建议动作，不要直接晋升。
```

当用户选择“沉淀”时，Agent 先记录该意向。审核通过后，compiler 才能把候选新建为
Wiki 页面，或合并到现有页面。敏感信息、凭证、未经验证的猜测不应进入 Inbox。

## 5. 写入链路验收

以下提示词会真实创建一条 Inbox 候选：

```text
请使用 km_propose_capture 创建一条真实候选，dry_run=false：
- title: AgentsKM Codex 0.5.3 验收
- type: note
- value_reason: 验证 Codex 插件可以通过官方 PyPI runtime 写入公共 Inbox
- body: Codex 官方插件应通过 MCP 调用受权限控制的 CLI，将候选写入用户配置指定的 Vault。
- source_session: codex-0.5.3-acceptance
- agent_id: codex
- source_tool: codex-plugin

完成后报告 candidate_id 和文件路径，但不要自动 review、promote 或 merge。
```

确认来源字段和内容无误后，再让 Codex 对指定 `candidate_id` 执行审核及晋升。测试候选
是否保留由用户决定；AgentsKM 默认保留 Inbox 审计记录，而不是直接删除文件。

## 6. 更新

先刷新官方 Marketplace，再重新安装插件：

```powershell
codex plugin marketplace upgrade agentskm-official
codex plugin add agentskm-toolkit@agentskm-official
```

然后开启新会话并重新执行 `km_doctor`。`km_update` 可以报告更新状态，但正在运行的
PyPI 进程不能原地替换自身；以新会话报告的 Toolkit version 为最终依据。

## 7. 卸载和重装

卸载插件不会删除用户 Vault 或 `~/.agentskm/config.json`：

```powershell
codex plugin remove agentskm-toolkit@agentskm-official
```

如需同时移除 Marketplace 来源：

```powershell
codex plugin marketplace remove agentskm-official
```

重新安装时再次执行“全新安装”中的两条命令。不要为了重装插件删除 Vault。

## 8. 常见判断

- 能调用 `km_doctor` 且版本、Profile、Vault 正确，说明核心插件链路可用。
- Codex UI 未显示 `/km-doctor`，不代表 MCP 或 Skill 未加载；自然语言触发和 MCP
  工具是产品契约。
- 如果工具调用被宿主审批层拦截，应批准或修复宿主审批配置，不要绕过 MCP 直接写
  Vault。
- 如果修改了 Profile 角色但工具列表没变化，请重连 MCP 或开启新会话。
- 如果提示 Marketplace 已从不同来源添加，先核对来源；确需替换时，移除旧来源后
  再按正式命令添加。

