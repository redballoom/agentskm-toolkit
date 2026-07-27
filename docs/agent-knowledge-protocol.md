# Agent Knowledge Protocol

> 版本：v0.1  
> 日期：2026-07-25  
> 适用范围：Codex、Claude Code、Cursor、HermesBot、影刀及其他接入 AgentsKM 的 Agent  
> 核心原则：Agent 可以自动发现和提交候选；正式 Wiki 写入必须经过用户批准或预授权规则

## 1. 角色

| 角色 | 允许操作 | 禁止操作 |
|---|---|---|
| 贡献者 Agent | 搜索 Wiki/Inbox/Raw；提出候选；写入 `000_Inbox/` | 直接写入 `wiki/`；修改 `purpose.md` / `SCHEMA.md` |
| 编译者 Agent | 在批准范围内毕业或合并候选；更新 `wiki/`、`index.md`、`log.md` | 扩大用户批准范围；保存敏感凭证 |
| 巡检者 Agent | 检查断链、重复、过时、来源缺失；生成报告 | 默认不自动改正式知识 |
| 用户 | 批准毕业、拒绝、暂缓、仲裁冲突、修改宪法级规则 | 无 |

## 2. 知识分层

| 层级 | 目录 | 含义 |
|---|---|---|
| Raw | `raw/` | 原始资料、网页、日志、测试证据；尽量不可变 |
| Inbox | `000_Inbox/` | Agent 自动捕获的候选知识；未审核或审核记录 |
| Wiki | `wiki/` | 已审核、去重、建立链接的正式知识 |
| Docs | `docs/` | 架构计划、协议、操作手册、ADR |

默认查询顺序：

1. 先查 `wiki/`，优先使用正式知识。
2. 再查 `000_Inbox/`，必须标注“未审核候选”或“已毕业记录”。
3. 最后查 `raw/`，作为证据来源，不直接当作结论。

## 3. 候选捕获标准

Agent 发现以下内容时，应提出候选：

- 可跨项目复用的技术方案、踩坑经验、调试路径。
- 对工具选择、架构边界、权限规则有长期影响的判断。
- 从原始资料中提取出的稳定 API、流程、限制或模式。
- 用户明确说“这个要记住 / 以后复用 / 沉淀一下”。

Agent 不应捕获以下内容：

- 密钥、token、账号、客户隐私、个人敏感信息。
- 一次性业务细节，除非能抽象为通用模式。
- 没有复用价值的临时聊天。
- 来源不明且容易过时的事实，除非标为低置信候选。

## 4. 候选 Frontmatter v1

所有新候选必须使用以下字段：

```yaml
---
id: kmc-YYYYMMDD-NNNN
title: 候选标题
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: pending
type: entity | concept | comparison | query | guide | note
tags: [implicit-capture, ...]
agent_id: codex
source_tool: codex-desktop
source_session: session-id-or-reference
source_refs:
  - raw/articles/example.md
suggested_action: create | merge | hold | reject
suggested_target: wiki/queries/example.md
value_reason: 这条知识为什么值得沉淀
confidence: high | medium | low
sensitivity: normal | sensitive | secret
fingerprint: sha256-of-normalized-topic-and-claims
---
```

兼容规则：

- 旧字段 `sources` 可以暂时保留，但新写入必须使用 `source_refs`。
- 如果 `source_refs` 为空，候选不能直接毕业，只能进入 `pending-source-review`。
- `sensitivity: secret` 的候选不得写入 Wiki，只能提示用户处理。

## 5. 状态机

```text
pending
  -> reminded
    -> approved -> graduated | merged
    -> snoozed
    -> rejected
  -> duplicate -> merged | rejected
  -> pending-source-review
```

状态含义：

| 状态 | 含义 |
|---|---|
| `pending` | 已捕获，尚未提醒 |
| `reminded` | 已向用户提醒 |
| `approved` | 用户已批准毕业或合并 |
| `graduated` | 已创建正式 Wiki 页 |
| `merged` | 已合并到现有 Wiki 页 |
| `snoozed` | 暂缓处理 |
| `rejected` | 明确不沉淀 |
| `duplicate` | 与已有候选或 Wiki 重复 |
| `pending-source-review` | 有价值但来源不足，需补证据 |

## 6. 提醒格式

Agent 提醒用户时使用这个最小格式：

```text
发现一条值得沉淀的知识：{title}
价值：{value_reason}
建议：{suggested_action} -> {suggested_target}
依据：{source_refs 或证据摘要}
风险：{sensitivity / confidence}
请选择：沉淀 / 稍后 / 忽略
```

同一 `fingerprint` 在内容没有实质变化时不得重复提醒。

## 7. 毕业规则

从 Inbox 到 Wiki 必须满足：

- 用户明确批准，或命中用户提前授权的具体自动化规则。
- `source_refs` 至少有一项，或者候选本身是对话内可追溯的审计记录。
- 不包含密钥、token、客户隐私、个人敏感信息。
- 目标路径位于 `wiki/entities/`、`wiki/concepts/`、`wiki/comparisons/` 或 `wiki/queries/`。
- `index.md` 和 `log.md` 同步更新。

毕业后：

- Inbox 文件不删除，状态改为 `graduated` 或 `merged`。
- 正式 Wiki 页写入 `origin_candidate`。
- `log.md` 记录批准来源、目标路径和变更范围。

## 8. 多 Agent 并发约定

在 KM CLI 未完成前：

- 同一时间只允许一个编译者 Agent 执行毕业。
- 贡献者 Agent 可以写 Inbox，但应避免修改同一个候选文件。
- 正式页写入前先检查目标文件是否已存在。

KM CLI 完成后：

- 所有写入通过 `km propose`、`km promote`、`km lint` 执行。
- Agent 或适配层需要机器输出时，应调用 `--json`。
- CLI 负责文件锁、事务、幂等和审计。
- MCP、HTTP、Obsidian CLI 都只能作为薄适配层调用 KM CLI。
- HTTP 适配器只允许本机监听，默认 `127.0.0.1`，不得作为公网服务暴露。
- MCP 适配器使用 stdio 传输，只暴露 tools，不直接读写 Markdown。
- 日常操作和验收步骤见 `docs/operations-runbook.md`。
- qmd 只在阈值和就绪报告都满足时再启用；默认继续使用基础搜索。

## 9. 当前默认策略

截至 2026-07-25：

- Codex 可在本仓库改造期临时扮演编译者 Agent。
- `lingxing-api-auth.md` 已批准毕业。
- `wsl-chrome-cdp-setup.md` 已批准毕业。
- `ai-agent-platform-comparison-2025.md` 暂缓毕业，需补来源。
- 根目录 `concepts/` 不再作为正式知识目录；正式概念页进入 `wiki/concepts/`。
- Obsidian 审核入口为 `docs/review-dashboard.md`，通过 `km dashboard` 刷新。
