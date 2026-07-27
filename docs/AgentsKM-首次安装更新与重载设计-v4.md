# AgentsKM 首次安装、更新与重载设计 v4

> 日期：2026-07-27
> 状态：已实现并纳入 `0.4.2`

## 目标

让新电脑上的用户只安装插件即可进入可用状态，同时保留自由迁移 Vault、
多 Agent 共用 Inbox、角色隔离、可诊断和可更新能力。

## 首次安装

插件安装后的第一次 MCP 启动执行一次幂等 bootstrap：

1. 读取 `%USERPROFILE%\.agentskm\config.json`。
2. 配置不存在时，通过内置 CLI 创建配置和当前 Agent Profile。
3. 创建 `%USERPROFILE%\Documents\AgentsKM\vault` 作为默认空 Vault。
4. 空 Vault 包含 README、index、`000_Inbox/`、`wiki/`、`raw/`、`docs/`。
5. 当前 MCP 进程继续加载完整工具，无需为 Setup 重启。

Codex 插件默认创建 `codex/compiler`。Hermes、Claude、Cursor 和通用 MCP
安装默认创建各自的 `contributor` Profile。已有 legacy、无效或冲突配置不会
自动覆盖，只开放 Setup、Doctor 和 Update 工具用于恢复。

## 配置来源

配置文件是 Vault、Profile 和角色的唯一运行时事实来源：

```text
%USERPROFILE%\.agentskm\config.json
```

不读取 `AGENTSKM_CONFIG`、`AGENTSKM_PROFILE`、`AGENTSKM_ROLE` 或
`AGENTSKM_DATA_ROOT` 来决定运行身份。MCP 启动参数显式选择 Profile；CLI 的
`--config` 仅用于隔离测试和诊断。

用户把 `vaults.main.path` 改为另一个有效 AgentsKM Vault 后，后续调用立即指向
新路径。CLI 与 MCP 每次操作都重新解析配置，不缓存 Vault 路径或角色。

## 公共 Inbox 与来源

连接同一 Vault 的所有 Profile 共用 `000_Inbox/`。每个候选在 frontmatter
开头记录：

```yaml
agent_id: codex
source_tool: codex-mcp
source_session: conversation-id
source_refs:
  - conversation:conversation-id
```

相同指纹或目标的候选不会重复创建，而是合并 `contributor_agents`、
`source_sessions` 和 `source_refs`。Wiki 仍只能由 compiler 在明确审批后写入。

## 更新

统一入口：

```powershell
python tools\km-cli\km.py update
```

- 源码仓库：检查工作区干净后，`fetch` 并 `--ff-only` 合并 GitHub `main`，
  然后重新构建自包含插件。
- Codex Git marketplace：先刷新 marketplace 快照，再重新安装插件。
- 其他没有宿主更新驱动的打包环境：明确返回重新安装 GitHub 包的动作，不覆盖
  正在运行的文件。

Skill 在用户明确要求更新时直接调用 `km_update`，不增加第二次确认。

## 重载策略

按变更类型区分：

| 变更 | 重载方式 |
| --- | --- |
| Vault 路径、Profile、角色、普通 Setup | 动态重读，无需重启 |
| Inbox/Wiki 内容 | 下一次调用直接可见 |
| 插件、CLI、MCP 或 Skill 代码更新 | MCP reconnect；不支持时新建会话 |

不由插件终止宿主进程，也不在知识写入事务中强制重启。对 Codex，代码升级后
新建会话是当前最可靠的冷重载边界。

## 快速诊断

`km doctor` 和 MCP 的 `km_doctor` 返回：

- Toolkit 版本和 GitHub 来源；
- 配置文件路径、Profile、角色和 Vault 路径；
- Vault 存在性、目录结构、可写性和 stale lock；
- 当前状态与 `next_action`。

这条命令是安装、迁移、角色或路径异常时的第一检查入口。
