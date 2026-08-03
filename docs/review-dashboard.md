# AgentsKM 审核面板

> 由 `agentskm dashboard` 生成。用于 Obsidian 中快速审核 Inbox、查看正式 Wiki 和 Raw 来源。

更新时间：2026-07-25T12:13:10

## 总览

| 层级 | 数量 |
|---|---:|
| Wiki 正式页 | 3 |
| Inbox 待处理 | 1 |
| Inbox 已毕业/已合并 | 2 |
| Inbox 已拒绝 | 0 |
| Raw 来源 | 3 |

## 待处理 Inbox

| 状态 | 类型 | 页面 | 标签 | 来源/目标 |
|---|---|---|---|---|
| pending-source-review | comparison | [AI Agent 平台对比分析（2025）](../000_Inbox/ai-agent-platform-comparison-2025.md) | implicit-capture, ai-agent, mcp, automation, workflow, comparison, research | wiki/comparisons/ai-agent-platform-comparison-2025.md |

## 已毕业或已合并 Inbox

| 状态 | 类型 | 页面 | 标签 | 来源/目标 |
|---|---|---|---|---|
| graduated | concept | [灵犀 API 认证机制（access_token）](../000_Inbox/lingxing-api-auth.md) | implicit-capture, api, auth, lingxing | wiki/queries/lingxing-api-auth.md |
| graduated | guide | [WSL 连接 Windows Chrome CDP 调试完整方案](../000_Inbox/wsl-chrome-cdp-setup.md) | implicit-capture, debugging, cdp, chrome, wsl, browser-automation | wiki/queries/wsl-chrome-cdp-setup.md |

## 正式 Wiki

| 状态 | 类型 | 页面 | 标签 | 来源 |
|---|---|---|---|---|
| active | concept | [从 Docsify 文档站点提取 API 清单的方法论](../wiki/concepts/docsify-api-extraction-methodology.md) | methodology, api, automation, web-scraping | raw/articles/lingxing-api-complete-catalog.md |
| active | query | [领星/灵犀 API 鉴权机制（access_token）](../wiki/queries/lingxing-api-auth.md) | api, auth, lingxing | raw/articles/lingxing-api-access-token-doc.md |
| active | query | [WSL 连接 Windows Chrome CDP 调试方案](../wiki/queries/wsl-chrome-cdp-setup.md) | debugging, cdp, chrome, wsl, browser-automation | 000_Inbox/wsl-chrome-cdp-setup.md |

## Raw 来源

| 状态 | 类型 | 页面 | 标签 | 来源 |
|---|---|---|---|---|
| - | - | [获取接口令牌 access_token](../raw/articles/lingxing-api-access-token-doc.md) | - | - |
| - | - | [灵犀 OpenAPI 完整接口清单](../raw/articles/lingxing-api-complete-catalog.md) | - | - |
| - | - | [灵犀 OpenAPI — 基础数据接口清单](../raw/articles/lingxing-basic-data-apis.md) | - | - |

## 操作入口

```powershell
python tools\km-cli\km.py pending
python tools\km-cli\km.py search "领星 API 鉴权"
python tools\km-cli\km.py validate
python tools\km-cli\km.py lint
```
