# AgentsKM Operations Runbook

> 日期：2026-07-25  
> 目标：让用户和各类 Agent 用同一套步骤查询、捕获、审核、毕业和验收知识库。

## 1. 日常查询

优先查正式 Wiki：

```powershell
python tools\km-cli\km.py search "领星 API 鉴权"
```

机器调用使用 JSON：

```powershell
python tools\km-cli\km.py search "领星 API 鉴权" --limit 3 --json
```

判断结果时：

- `[wiki]` 是已审核正式知识。
- `[inbox]` 是候选或审计记录，必须看 `status`。
- `[raw]` 是原始证据，不直接作为最终结论。

## 2. 查看待审

```powershell
python tools\km-cli\km.py pending
```

当前 Obsidian 审核面板：

```powershell
python tools\km-cli\km.py dashboard
```

打开：

```text
docs/review-dashboard.md
```

## 3. 提交候选

Agent 发现可复用知识时，先进入 Inbox：

```powershell
python tools\km-cli\km.py propose `
  --title "候选标题" `
  --type concept `
  --tags "api,auth" `
  --source-ref raw/articles/example.md `
  --suggested-target wiki/concepts/example.md `
  --value-reason "这条知识可跨项目复用" `
  --body "候选正文"
```

只预览不写入：

```powershell
python tools\km-cli\km.py propose `
  --title "候选标题" `
  --value-reason "验证" `
  --dry-run `
  --json
```

## 4. 毕业到 Wiki

毕业必须有明确批准范围：

```powershell
python tools\km-cli\km.py promote 000_Inbox/example.md `
  --target wiki/concepts/example.md `
  --approved-by user `
  --scope "用户明确批准：沉淀该候选为正式知识"
```

`promote` 会拒绝：

- 已经 `graduated` / `merged` / `rejected` 的候选。
- `sensitivity: secret` 的候选。
- 缺少 `source_refs` 的候选。
- 目标路径不在 `wiki/entities/`、`wiki/concepts/`、`wiki/comparisons/`、`wiki/queries/` 下。

## 5. HTTP 接入

启动本机 HTTP 适配器：

```powershell
python adapters\http\km_http.py --host 127.0.0.1 --port 8765
```

常用接口：

```text
GET  /status
GET  /pending
GET  /search?q=领星 API 鉴权&limit=1
POST /propose
POST /promote
```

HTTP 适配器只做参数翻译，所有规则仍由 KM CLI 执行。

## 6. MCP 接入

MCP server 配置示例：

```json
{
  "mcpServers": {
    "agentskm": {
      "command": "python",
      "args": ["D:/AgentsKM/adapters/mcp/km_mcp.py"]
    }
  }
}
```

暴露工具：

```text
km_status
km_pending
km_search
km_validate
km_lint
km_propose_capture
km_promote_candidate
km_dashboard
```

MCP 适配器只调用 `km.py --json`，不直接操作 Markdown。

## 7. 健康检查

```powershell
python tools\km-cli\km.py validate
python tools\km-cli\km.py lint
python tests\acceptance\test_km_workflow.py
python tools\km-cli\km.py qmd-readiness
```

验收通过时应看到：

```text
Validation passed.
Lint passed.
Acceptance workflow passed.
```

## 8. 故障定位

| 现象 | 优先检查 |
|---|---|
| 搜不到正式知识 | `python tools\km-cli\km.py search "关键词" --json` |
| 候选无法毕业 | 候选是否有 `source_refs`，是否 `sensitivity: secret`，是否已终态 |
| Dashboard 过时 | 运行 `python tools\km-cli\km.py dashboard` |
| qmd 是否该启用 | 运行 `python tools\km-cli\km.py qmd-readiness`，看阈值与固定查询命中率 |
| HTTP 不通 | 先查 `/health`，再确认端口只监听 `127.0.0.1` |
| MCP 工具不可见 | 先运行 `python adapters\mcp\km_mcp.py` 冒烟测试，确认配置路径是绝对路径 |
| 写入中断 | 查看 `.km/transactions/`，失败事务会记录 touched 文件和 rollback 结果 |

## 9. 当前已知事项

- `000_Inbox/ai-agent-platform-comparison-2025.md` 仍是 `pending-source-review`，需要补来源后才能毕业。
- `.km/` 是本地事务、锁和缓存目录，不提交 Git。
- `C:\Users\redballoon\.config\git\ignore` 当前有用户级 Git 权限警告，不影响仓库内校验。
