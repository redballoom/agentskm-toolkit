# AgentsKM 0.5.3 Obsidian 指南

Obsidian 是 AgentsKM Vault 的本地呈现入口。它负责浏览 Markdown、标签、链接和图谱；
AgentsKM CLI/MCP 仍是配置、权限、状态、审核、事务和审计的唯一写入入口。

## 1. 确认当前 Vault

不要假定或硬编码 Vault 目录。先用具备 reviewer 或 compiler 权限的 Profile 查询：

```powershell
agentskm doctor --profile codex --json
agentskm status --profile codex --json
```

使用返回的 `vault_path`。解析链为：

```text
选定 Profile
  -> profiles.<profile>.vault
  -> vaults.<vault-name>.path
```

`doctor` 应同时返回 `state: ready`。若使用 `uvx`，将命令前缀替换为：

```text
uvx --from agentskm-toolkit==0.5.3 agentskm
```

## 2. 在 Obsidian 中打开

在 Obsidian 选择 **Open folder as vault**，打开上一步返回的 `vault_path`。在 Files and
links 的 Excluded files 中排除：

```text
.km/
```

`.km/` 保存锁、事务和审计内部数据，不是知识浏览入口。`.obsidian/` 是本机界面配置，
不得提交到 Toolkit 仓库。

## 3. 生成审核面板

Dashboard 已包含在 0.5.3 中，只对 reviewer/compiler 开放。按需手动刷新：

```powershell
agentskm dashboard --profile codex
```

成功后在 Obsidian 打开：

```text
docs/review-dashboard.md
```

面板汇总当前非终态 Inbox、已毕业或已合并记录、正式 Wiki 和 Raw 来源。它是一次生成的
快照，不会自动刷新；候选变化后再次运行命令即可。到期提醒仍以 `km_reminders` 或
`agentskm reminders` 的结果为准。

## 4. 写入边界

- 可以使用 Obsidian 搜索、标签、图谱和链接导航。
- 不要直接修改候选状态、审核字段、Wiki frontmatter、索引或审计文件。
- 审核使用 `km_review_candidate` 或 `agentskm review`。
- 晋升和合并使用 `km_promote_candidate` / `km_merge_candidate`，或对应 CLI 命令。
- 直接编辑治理字段会绕过角色检查、敏感内容扫描、文件锁、事务和审计。

0.5.3 不会自动转储会话到 `raw/`，也不会在会话结束时自动写入 Inbox 或 Wiki。
