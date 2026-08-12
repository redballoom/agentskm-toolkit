# 呈现层与自动捕获层增强计划

> 状态: 0.5.3 呈现层动作已采纳；自动捕获增强延期
> 日期: 2026-08-12
> 范围: AgentsKM 0.5.3 呈现层启用与后续增强边界
> 前置文档: `permission-aware-capture-plan.md`（捕获交互契约）、`hermes-hook-pilot-handoff.md`（Hook 试点）

## 1. 背景与目标

AgentsKM 的 Vault 是纯 Markdown（frontmatter 标准 YAML），知识浏览主要依赖
CLI/MCP 文本输出。0.5.3 使用 Obsidian 作为低成本本地呈现入口，同时保持
AgentsKM 对配置、权限、状态、事务和审计的所有权。

本轮只启用已有能力并补齐说明，不新增自动持久化行为。

## 2. 0.5.3 已验证能力

- Vault 路径从 `~/.agentskm/config.json` 动态解析：选定 Profile 的 `vault` 字段
  引用 `vaults.<name>.path`。权威值以 `km_doctor` / `km_status` 返回的
  `vault_path` 为准，不得硬编码。
- 标准分层为 `000_Inbox` / `wiki/{concepts, comparisons, entities, queries}` /
  `raw` / `docs` / `.km`。
- frontmatter 使用标准 YAML，`tags` 为数组格式，可由 Obsidian 读取。
- Dashboard 已实现、通过验收并对 reviewer/compiler 开放；0.5.3 采用手动刷新，
  不新增后台任务。
- `raw/` 是可选证据层；0.5.3 不新增自动 Raw 写入接口或会话转储行为。

## 3. 分析结论

### 3.1 自动捕获层

当前流程保持不变：

```text
host Hook（Hermes 可用时）
  -> Skill 语义策略（已验证、可复用、非敏感、有证据、无重复）
  -> 最多提示一次：沉淀 / 稍后 / 忽略
  -> 用户显式意图（例如“沉淀这条”）直接进入权限感知流程
```

“候选 + 一次提示 + 显式意图 + 审核”是 AgentsKM 的治理边界。会话收尾评估和
Raw 证据捕获涉及新的持久化、安全、保留与去重契约，不属于 0.5.3。

### 3.2 呈现层

Obsidian 是 0.5.3 的本地呈现入口，用于浏览 Markdown、标签、链接和图谱。它不取代
AgentsKM 的状态机；候选审核、Wiki 写入和治理字段修改仍必须通过 CLI/MCP。

自建 Web UI 和 RAG 语义检索不在本轮范围内。

## 4. 动作与版本边界

| # | 动作 | 版本决策 | 具体内容 |
|---|---|---|---|
| 1 | Obsidian 打开配置中的 Vault | 0.5.3 文档启用 | 先通过 `km_doctor` 确认 `vault_path`，再 Open folder as vault；排除 `.km`，使用 Tags / Graph / 全文搜索浏览 |
| 2 | 手动刷新 Dashboard | 0.5.3 文档启用 | reviewer/compiler 按需运行 `agentskm dashboard --profile <profile>`，打开 `docs/review-dashboard.md` |
| 3 | Raw 层兜底 | 延期，不在 0.5.3 实施 | 先定义显式授权、敏感内容扫描、大小与保留期限、来源和审计，再决定是否增加受控证据写入接口 |
| 4 | 会话收尾强制评估 | 延期，不在 0.5.3 实施 | 只考虑非写入、幂等、失败不阻塞的宿主级评估；不得把收尾事件视为持久化授权 |
| 5 | 自动 wikilink | 延期，不在 0.5.3 实施 | 仅在目标页已确认存在时生成链接，并继续由 `km lint` 检查失效链接 |

## 5. 边界

- 不把捕获改成自动入库，保留候选、用户选择和审核流程。
- 不自建 Web UI，也不在本轮接入 RAG。
- 不改变 Vault 数据结构。
- Obsidian 作为浏览和审核入口；治理状态只能通过 AgentsKM CLI/MCP 修改。
- 不允许 Hook 绕过角色、候选状态、审批或安全检查。

## 6. 0.5.3 决策

- [x] 使用 Obsidian 打开动态解析出的 Vault，并提供独立使用指南。
- [x] 保留现有 `km_dashboard` 行为，采用 reviewer/compiler 手动刷新。
- [x] 不在 0.5.3 实现 Raw 自动转储、会话收尾强制评估或自动 wikilink。
- [x] 不在 Obsidian 中直接修改候选状态、frontmatter 或 Wiki 治理字段。
- [x] 本文档保留在 `docs/`，作为本轮范围决策记录。
