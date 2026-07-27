# AgentsKM P0 基线盘点报告

> 日期：2026-07-25  
> 阶段：P0 / Phase 0  
> 操作性质：只读盘点后生成报告；未迁移、未删除、未改写知识页  
> 对应计划：`docs/AgentsKM-架构改造执行计划.md`

## 1. 当前 Git 基线

- 当前分支：`master`
- 最新提交：`80ff8cb feat: .learnings/ 目录初始化（self-improvement 集成）`
- 当前工作区已有变更：
  - `M index.md`
  - `M log.md`
  - `?? 000_Inbox/ai-agent-platform-comparison-2025.md`
  - `?? docs/`
- 保护原则：
  - 不覆盖、回退、删除上述已有变更。
  - 迁移正式知识前先列出目标，由用户确认。
  - 后续 CLI 或脚本写入必须保留审计记录。

## 2. 仓库结构现状

根目录当前包含：

```text
000_Inbox/
concepts/
docs/
raw/
wiki/
.learnings/
.obsidian/
index.md
log.md
purpose.md
SCHEMA.md
```

关键观察：

- `wiki/` 已存在分类目录，但当前没有 Markdown 文件。
- `concepts/` 目前承载了一个看起来像正式知识的页面。
- `000_Inbox/` 中已有 3 条候选知识。
- `raw/articles/` 中已有 3 条领星 OpenAPI 原始资料。
- `.obsidian/` 已存在，说明该仓库已作为 Obsidian vault 使用过。
- `.learnings/` 是 self-improvement 相关目录，暂不纳入 Wiki 正式知识迁移。

## 3. Markdown 文件清单

| 层级 | 文件数 | 说明 |
|---|---:|---|
| 根目录治理文件 | 4 | `index.md`、`log.md`、`purpose.md`、`SCHEMA.md` |
| `docs/` | 1 | 已生成架构改造执行计划 |
| `000_Inbox/` | 3 | 未审核候选知识 |
| `raw/articles/` | 3 | 原始资料层 |
| 根目录 `concepts/` | 1 | 当前疑似正式知识，但不在 `wiki/` 下 |
| `wiki/` | 0 | 目标正式知识层尚未落页 |
| `.learnings/` | 3 | 隐藏运行学习目录，暂不作为 Wiki 内容 |

主要内容页：

| 路径 | 标题 | 初步定位 |
|---|---|---|
| `000_Inbox/lingxing-api-auth.md` | 灵犀 API 认证机制 | 候选，建议毕业或合并为领星 API 鉴权正式页 |
| `000_Inbox/wsl-chrome-cdp-setup.md` | WSL 连接 Windows Chrome CDP 调试完整方案 | 候选，建议毕业为浏览器自动化/调试指南 |
| `000_Inbox/ai-agent-platform-comparison-2025.md` | AI Agent 平台对比分析（2025） | 候选，建议先补来源再决定是否毕业 |
| `concepts/docsify-api-extraction-methodology.md` | 从 Docsify 文档站点提取 API 清单的方法论 | 疑似正式知识，建议迁入 `wiki/concepts/` |
| `raw/articles/lingxing-api-access-token-doc.md` | 获取接口令牌 access_token | 原始来源，可作为领星鉴权页证据 |
| `raw/articles/lingxing-api-complete-catalog.md` | 灵犀 OpenAPI 完整接口清单 | 原始来源 |
| `raw/articles/lingxing-basic-data-apis.md` | 灵犀 OpenAPI — 基础数据接口清单 | 原始来源 |

## 4. Inbox 状态

当前 Inbox 候选：

| 候选 | 当前质量 | 建议动作 |
|---|---|---|
| `000_Inbox/lingxing-api-auth.md` | 高置信，有明确 raw 来源 | 优先毕业到 `wiki/queries/lingxing-api-auth.md` 或 `wiki/concepts/lingxing-api-auth.md` |
| `000_Inbox/wsl-chrome-cdp-setup.md` | 高置信，实践细节完整 | 毕业到 `wiki/queries/wsl-chrome-cdp-setup.md` 或 `wiki/concepts/browser-cdp-debugging.md` |
| `000_Inbox/ai-agent-platform-comparison-2025.md` | 中等置信，`sources: []` | 先补来源或降级保留，暂不建议直接毕业 |

注意：

- 现有候选使用的是旧字段 `sources`，计划中的新契约要求 `source_refs`、`agent_id`、`source_tool`、`source_session`、`status`、`fingerprint` 等字段。
- 因此下一步不应直接移动文件，而应先补齐候选 Schema 或由 `km propose`/迁移脚本统一升级。

## 5. 链接检查

发现的未解析 Wikilink：

| 来源 | 目标 | 判断 |
|---|---|---|
| `000_Inbox/lingxing-api-auth.md` | `[[灵犀 API 全貌]]` | 待创建正式概念页 |
| `000_Inbox/lingxing-api-auth.md` | `[[OpenAPI 认证模式对比]]` | 待创建正式概念页 |
| `purpose.md` | `[[Excel-to-Web-Form-Automation]]` | 示例性占位链接 |
| `purpose.md` | `[[Shadow-DOM-Element-Scraping]]` | 示例性占位链接 |
| `SCHEMA.md` | `[[wikilinks]]` | 文档示例，不应当作真实页面 |
| `docs/AgentsKM-架构改造执行计划.md` | `[[wikilinks]]` | 文档示例，不应当作真实页面 |

孤儿页初步结果：

| 页面 | 判断 |
|---|---|
| `raw/articles/lingxing-api-access-token-doc.md` | 未被 Markdown 正文链接显式引用，但被 Inbox frontmatter 的旧 `sources` 字段引用；后续应转为 `source_refs` |

## 6. 目录双轨问题

当前存在一个结构性不一致：

- 计划目标：正式知识统一进入 `wiki/`。
- 当前现状：`concepts/docsify-api-extraction-methodology.md` 位于根目录 `concepts/`。
- 风险：后续 Agent 搜索和写入时会混淆“根目录 concepts”与“wiki/concepts”。

建议迁移目标：

| 当前路径 | 建议目标 | 处理方式 |
|---|---|---|
| `concepts/docsify-api-extraction-methodology.md` | `wiki/concepts/docsify-api-extraction-methodology.md` | 用户确认后迁移，并更新 `index.md` 链接 |

## 7. 优先验收查询

计划中的关键验收查询：

> 领星 API 怎么鉴权

当前状态：

- 能在 `000_Inbox/lingxing-api-auth.md` 找到较完整答案。
- 但该答案仍是 Inbox 候选，不应被标记为正式 Wiki。
- `raw/articles/lingxing-api-access-token-doc.md` 可作为证据来源。
- `wiki/` 中尚无正式答案页。

建议 P1 目标：

- 将 `000_Inbox/lingxing-api-auth.md` 审核毕业为正式 Wiki 页。
- 将 `sources` 升级为 `source_refs`。
- 在搜索结果中明确区分：
  - Wiki：已审核正式知识
  - Inbox：未审核候选
  - Raw：原始证据

## 8. 下一步建议

建议按以下顺序继续：

1. 先确认目录迁移策略：
   - 是否将根目录 `concepts/` 的正式页迁入 `wiki/concepts/`。
2. 先确认现有 Inbox 处理：
   - `lingxing-api-auth.md`：毕业 / 合并 / 保留 / 拒绝。
   - `wsl-chrome-cdp-setup.md`：毕业 / 合并 / 保留 / 拒绝。
   - `ai-agent-platform-comparison-2025.md`：补来源后再审 / 保留 / 拒绝。
3. 再实现候选 Schema 与 Agent 协议：
   - `docs/agent-knowledge-protocol.md`
   - 候选 frontmatter v1
   - 用户批准记录格式
4. 最后实现 `tools/km-cli/` 的最小闭环：
   - `km status`
   - `km validate`
   - `km propose`
   - `km pending`
   - `km promote`
   - `km search`
   - `km lint`

## 9. 本阶段结论

P0 基线显示：当前仓库规模小、结构清晰，适合直接按改造计划推进。最需要先处理的不是引入复杂检索，而是先完成三件事：

1. 统一正式知识目录到 `wiki/`。
2. 将现有 Inbox 升级到统一候选契约。
3. 用 KM CLI 接管正式写入，避免多 Agent 直接改写 Wiki。

