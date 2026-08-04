# AgentsKM 0.5.2 使用指南

AgentsKM 将多个 Agent 对话中可复用的结论先提交到公共 Inbox，再由具备权限的
Profile 审核并写入 Wiki。知识文件保存在用户自己的 Vault 中，不随插件或 Python
包上传。

## 选择入口

| 使用者 | 安装方式 | 默认 Profile / 角色 | 指南 |
| --- | --- | --- | --- |
| Codex 用户 | GitHub Marketplace 插件 | `codex` / `compiler` | [Codex 插件指南](codex.md) |
| Hermes、Claude、Cursor 等 Agent | PyPI runtime + stdio MCP | 每个宿主独立 Profile / `contributor` | [通用 MCP 与多 Agent 指南](mcp-hosts.md) |
| 终端或自动化脚本用户 | `uvx` 或 `uv tool install` | 显式选择 Profile | [CLI 指南](cli.md) |
| 仓库维护者 | 源码 checkout | 临时测试配置与 Vault | [维护与发布指南](maintainer.md) |

最终用户只需要选择一种入口，不需要克隆 Toolkit 仓库。Codex 插件会注册 Skill 和
MCP；其他 Agent 在首次启动 MCP 时由 `uvx` 自动取得 PyPI runtime。

## 共同前置条件

- Python runtime 由 `uvx` 管理，AgentsKM 要求 Python 3.10 或更高版本。
- `uvx` 必须位于宿主进程的 `PATH` 中，可先运行 `uvx --version` 验证。
- Codex 用户还需要能够运行 `codex plugin --help`。
- 不使用 `AGENTSKM_DATA_ROOT` 等环境变量选择 Vault；配置文件是唯一配置来源。

默认位置：

```text
config: ~/.agentskm/config.json
Vault:  ~/Documents/AgentsKM/vault
```

Windows 中对应：

```text
config: %USERPROFILE%\.agentskm\config.json
Vault:  %USERPROFILE%\Documents\AgentsKM\vault
```

首次 MCP 启动会在缺失时创建配置、Profile 和空 Vault。已有配置不会被冲突参数
静默覆盖。

## 角色和职责

| 角色 | 能力 | 推荐使用者 |
| --- | --- | --- |
| `contributor` | 搜索、提交候选、记录用户的沉淀/稍后/忽略选择 | Hermes、Claude、Cursor 和一般 Agent |
| `reviewer` | contributor 能力，加审核和 Dashboard | 专用审核 Agent 或人工审核入口 |
| `compiler` | reviewer 能力，加晋升和合并 Wiki | 可信 Codex Profile |

所有 Profile 可以指向同一个 Vault，因此共享 Inbox 和 Wiki；每条候选仍记录
`agent_id`、`source_tool`、`source_session` 和来源引用。角色既影响 MCP 可见工具，
也由 CLI 在真正写入前再次校验。

## 标准使用链路

```text
对话产生已验证的可复用结论
  -> Agent 搜索是否已有同类知识
  -> contributor 提交一条 Inbox 候选
  -> 用户选择：沉淀 / 稍后 / 忽略
  -> reviewer 审核候选
  -> compiler 将 approved 候选 promote 或 merge 到 Wiki
```

Inbox 是待审核事实来源，Wiki 是已审核知识。不要让 Agent 直接编辑 Vault Markdown
来绕过 MCP、锁、权限、敏感内容检查或审计记录。

## 最小验收标准

每个新宿主至少完成以下检查：

1. `km_doctor` 返回 `toolkit_version: 0.5.2` 和 `state: ready`。
2. Profile、Role、Config path 和 Vault path 与预期一致。
3. contributor 可以看到 `km_propose_capture`，看不到 review/promote/merge 工具。
4. compiler 可以看到完整工具集。
5. 一条真实候选能够进入公共 Inbox，并保留正确的 Agent 来源。

配置、角色、版本或插件发生变化后，应重新连接 MCP 或开启新会话。MCP 工具列表在
一次连接期间固定，不以宿主是否显示 `/km-doctor` 作为安装成功标准。

