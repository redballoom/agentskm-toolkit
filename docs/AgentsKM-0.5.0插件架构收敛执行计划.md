# AgentsKM 0.5.0 插件架构收敛执行计划

> 状态：已完成（0.5.0 已发布；发布收尾缺口转入 0.5.1 修复）
>
> 日期：2026-08-03
>
> 适用仓库：`redballoom/agentskm-toolkit`
>
> 当前基线：分支 `codex/plugin-pypi-runtime`，提交 `7fba1dc`
>
> 目标版本：`0.5.0`

## 1. 目标

将 AgentsKM 收敛为一套职责清晰、可测试、可一次安装的产品：

```text
GitHub Marketplace Plugin
  ├─ 安装 Codex Skill
  └─ 注册 MCP 启动配置
       └─ uvx 按需获取 PyPI Runtime
            ├─ agentskm CLI
            ├─ AgentsKM MCP Server
            └─ Vault 核心逻辑
```

用户仍只需安装一个 Codex 插件。插件不复制 CLI/MCP 源码；第一次启动 MCP
时由 `uvx` 获取固定版本的 PyPI 包。Vault 和用户配置始终独立于插件缓存、
uv 缓存与代码仓库。

### 1.1 成功标准

- Marketplace 安装后，Codex 能发现一个正式 AgentsKM Skill 和一个 MCP Server。
- 新机器无需克隆仓库，无需全局安装 `agentskm`。
- `uvx` 首次启动能获取固定版本的 CLI/MCP 运行时。
- CLI 是所有配置、权限、Vault 写入、锁、事务和审计规则的唯一执行入口。
- MCP 只负责工具 Schema、角色可见性、参数转换和结构化返回。
- Skill 只负责触发、工具选择、对话交互和用户批准边界。
- 源码、wheel、uvx、插件安装四种入口通过同一套行为验收。
- 插件、PyPI、CLI、MCP 的发布版本一致。

## 2. 不在 0.5.0 范围内

以下建议暂不实施，除非出现真实需求或性能数据：

- 不增加 MCP `resources`；需要读取正文时优先增加受控的 `km_read_page` 工具。
- 不增加 MCP `prompts`；提示与工作流由 Skill 管理。
- 不为 MCP 增加异步并发写入；写操作继续依赖 CLI 锁与事务串行化。
- 不为 `km_search` 增加时间缓存，避免多 Agent 共享 Vault 时读取过期状态。
- 不将 CLI/MCP 源码复制回插件。
- 不让插件自动安装 Python、修改 PATH 或全局安装 CLI。
- 不进行大规模 UI、HTTP 公网服务或 qmd 默认启用改造。

## 3. 当前仓库现状

### 3.1 当前分发链路

| 层级 | 当前实现 | 状态 |
|---|---|---|
| Marketplace | `.agents/plugins/marketplace.json` | 可用 |
| Codex Plugin | `plugins/agentskm-toolkit` | 可用，仍有迁移层 |
| Skill | `skills/agentskm-capture/SKILL.md` | 可用，职责名称偏窄 |
| Commands | `commands/km-*.md` | 被 Codex 转为 `source-command-*` Skill |
| MCP 启动 | `.mcp.json` 调用 `uvx` | 可用 |
| PyPI Runtime | `agentskm-toolkit==0.4.4` | 已发布并验证 |
| 用户配置 | `%USERPROFILE%/.agentskm/config.json` | 可用 |
| 默认 Vault | `%USERPROFILE%/Documents/AgentsKM/vault` | 可用 |

### 3.2 已确认问题

| 编号 | 问题 | 影响 | 优先级 |
|---|---|---|---|
| P-01 | Plugin `0.4.5`，PyPI/CLI/MCP `0.4.4` | 用户难以判断实际运行版本 | P0 |
| P-02 | `commands/` 被转换为 `source-command-*` | UI 名称不可控，和正式 Skill 重复 | P0 |
| P-03 | `src/` 与旧 `tools/`、`adapters/` 有重复实现 | 测试与发布运行时可能漂移 | P0 |
| P-04 | 只有发布工作流，没有普通 PR CI | 已知问题可能进入发布分支 | P0 |
| P-05 | 部分集成文档仍引用源码路径 | 新用户按文档无法获得产品化入口 | P0 |
| P-06 | MCP bootstrap 失败可能被静默忽略 | 用户只能看到后续 bootstrap-mode 错误 | P0 |
| P-07 | 顶层 CLI 帮助未完整呈现公开命令 | CLI 自解释能力不足 | P1 |
| P-08 | MCP 工具列表可随 Profile 状态变化，但未通知宿主 | 长会话可能缓存旧工具列表 | P1 |
| P-09 | `km.py` 体积大、职责较多 | 后续维护成本增加 | P2 |

### 3.3 当前值得保留的设计

- CLI 统一执行写入、权限、锁、事务和审计。
- MCP 使用 stdio，只暴露结构化工具。
- Profile 从配置文件推导角色，不接受调用方临时提权。
- contributor、reviewer、compiler 逐级增加能力。
- Plugin 不包含 Vault、用户配置或运行时源码副本。
- `uvx --from agentskm-toolkit==<version>` 提供隔离且可复现的运行时。
- Vault、代码仓库、插件缓存和 uv 缓存相互独立。

## 4. 目标职责边界

### 4.1 CLI

CLI 是唯一业务执行入口，负责：

- Setup、Profile、Vault 和配置解析。
- 搜索、候选捕获、响应、审核、毕业与合并。
- 角色权限、目标路径和敏感信息校验。
- 文件锁、事务、幂等、去重和审计。
- 稳定的文本帮助、JSON 输出和退出码。

CLI 不负责：

- 判断一段对话是否值得沉淀。
- 决定如何向用户提出“沉淀 / 稍后 / 忽略”。
- 暴露 Agent 特定的 UI 或插件元数据。

### 4.2 MCP

MCP 是 CLI 的 Agent 协议适配层，负责：

- 声明工具名称、描述和 JSON Schema。
- 根据固定 Profile 控制工具可见性。
- 将工具参数转换为 CLI 调用。
- 将 CLI JSON 结果包装为 MCP `structuredContent`。
- 将 bootstrap 错误和下一步操作完整返回给 Agent。

0.5.0 继续允许 MCP 通过子进程调用 CLI。没有性能证据前，不改为缓存或
并发直调。若未来抽取共享服务层，应先定义“服务层是唯一业务事实来源”，
再让 CLI 和 MCP 同时调用，避免形成两套规则。

### 4.3 Skill

Skill 是智能调度层，负责：

- 从用户自然语言识别 Setup、Doctor、Search、Capture、Review、Promote、Merge 意图。
- 在任务开始时决定是否先搜索 Wiki。
- 在任务结束时判断是否出现可复用知识。
- 调用正确的 MCP 工具，并遵守 Profile 权限。
- 向用户呈现候选价值并询问“沉淀 / 稍后 / 忽略”。
- 阻止未批准毕业、直接编辑 Markdown、保存秘密或绕过 MCP。

Skill 不实现 CLI 参数解析、文件写入、Frontmatter、锁或事务。

### 4.4 Plugin

Plugin 是一次安装的宿主装配包，只包含：

- `.codex-plugin/plugin.json`
- `.mcp.json`
- 一个正式 AgentsKM Skill 及必要 references/UI metadata

插件不包含 CLI、MCP Python 源码、Vault、用户配置、发布说明或开发文档。

## 5. 目标目录

### 5.1 Plugin 目录

```text
plugins/agentskm-toolkit/
├── .codex-plugin/
│   └── plugin.json
├── .mcp.json
└── skills/
    └── agentskm/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        └── references/
            ├── capture-workflow.md
            ├── setup-and-profiles.md
            └── roles-and-approval.md
```

删除：

```text
plugins/agentskm-toolkit/commands/
plugins/agentskm-toolkit/README.md
plugins/agentskm-toolkit/skills/agentskm-capture/
```

删除旧 Skill 目录时，将有效内容迁移到 `skills/agentskm/`，不是直接丢弃。

### 5.2 Python 包

```text
src/agentskm_toolkit/
├── __init__.py
├── __main__.py
├── cli.py
├── km.py
├── km_config.py
└── mcp.py
```

0.5.0 先确立 `src/agentskm_toolkit` 为唯一发布与测试源码。`km.py` 的模块化
拆分放到后续独立 PR，避免同时改变架构、行为和文件布局。

## 6. 分阶段执行

## Phase 0：建立保护网

目标：在结构改动前建立自动验收和版本契约。

### 改动

- 新增 `.github/workflows/ci.yml`。
- 触发条件：`pull_request`、推送到 `main` 和产品化分支。
- 在 Python 3.10、3.11、3.12 运行验收。
- 构建 wheel/sdist，并执行 `twine check`。
- 从 wheel 验证 `agentskm --version`、Setup 和 MCP tools/list。
- 运行插件 schema 校验、Skill 校验和 `scripts/build_plugin.py --check`。
- 新增版本一致性检查脚本，校验：
  - `pyproject.toml`
  - `agentskm_toolkit.__version__`
  - CLI `--version`
  - MCP `serverInfo.version`
  - `plugin.json`
  - `.mcp.json` PyPI pin
- 增加仓库纯度检查，拒绝 Vault、config、凭证、缓存和构建产物。

### 退出条件

- PR 创建后自动运行 CI。
- 当前基线在 CI 中通过。
- 人为制造一个版本不一致时，CI 必须失败。

## Phase 1：单一运行时源码

目标：确保发布、测试和开发调用相同实现。

### 改动

- 将 `src/agentskm_toolkit` 标记为唯一事实来源。
- 修改测试，优先调用：
  - `python -m agentskm_toolkit`
  - 构建后的 wheel
  - `uvx --from <wheel>`
- 审计 `tools/km-cli`、`adapters/mcp` 与 `src` 的差异。
- 删除旧副本，或临时保留为只导入包实现的兼容包装器。
- 不允许兼容包装器包含业务逻辑。
- 明确 HTTP adapter 的产品地位：
  - 若继续支持，迁入包内并纳入 wheel 验收；
  - 若不是 0.5.0 产品能力，标为实验性且不宣称随 PyPI 安装。
- 更新 `render_mcp_config.py`，默认只生成 `uvx`/已安装包入口。

### 退出条件

- 核心实现只存在一份。
- 源码、wheel 与 uvx 使用同一模块。
- 删除任一旧路径不会影响产品验收。

## Phase 2：CLI 与 bootstrap 契约

目标：让 CLI 可独立使用、可诊断，并为 MCP 提供稳定契约。

### 改动

- 顶层 `agentskm --help` 列出所有公开命令。
- 每个子命令提供用途、参数、默认值和退出码说明。
- 统一 JSON 结果：

```json
{
  "ok": false,
  "error": "human-readable message",
  "error_type": "StableErrorType",
  "next_action": "machine-readable-next-step"
}
```

- bootstrap 失败时保存并返回原始错误，不再静默 `return`。
- `doctor` 输出运行时版本、Profile、角色、配置路径、Vault 路径和失败检查。
- 保持写命令的角色校验、路径边界、敏感信息拒绝和审计不变。
- 为帮助文本、JSON 错误和 bootstrap 失败增加回归测试。

### 退出条件

- 一个未配置的新环境能从 CLI 错误中得到明确下一步。
- MCP 能原样返回 bootstrap 根因。
- 所有公开 CLI 命令都有 `--help` 验收。

## Phase 3：MCP 收敛

目标：保持薄适配，同时修复动态能力和错误可见性。

### 改动

- MCP 工具继续调用 CLI JSON 接口，不复制业务规则。
- 校验每个工具 description、Schema、required 字段和角色边界。
- 统一 contributor、reviewer、compiler 工具矩阵测试。
- 对工具列表变化选择并固定一种策略：
  - 推荐 0.5.0 使用“Profile/角色变化后要求重连 MCP”；
  - 不在运行中静默改变宿主已经缓存的工具列表。
- Setup 完成后返回 `restart_required` 或 `reconnect_required` 的明确状态。
- 暂不增加 resources、prompts、并发和搜索缓存。

### 退出条件

- 未配置、contributor、reviewer、compiler 四种工具列表有快照测试。
- 所有 MCP 错误包含可理解原因和下一步。
- MCP 无直接 Markdown 写入路径。

## Phase 4：Skill 渐进式披露

目标：一个正式 Skill 覆盖完整领域，同时减少常驻和触发后上下文。

### 改动

- 将 Skill 名称从 `agentskm-capture` 收敛为 `agentskm`。
- `SKILL.md` frontmatter 只保留：

```yaml
---
name: agentskm
description: <能力、使用场景和触发词的完整描述>
---
```

- description 覆盖：首次设置、配置异常、Profile、Vault、权限、搜索、候选捕获、
  稍后、忽略、审核、毕业和合并。
- `SKILL.md` 目标 60–100 行，只保留：
  - 使用 MCP，不直接编辑 Vault Markdown；
  - 搜索、捕获、用户决定主流程；
  - 安全和批准不可绕过规则；
  - 什么时候读取哪份 reference。
- `capture-workflow.md` 保存候选判断、提醒和用户决定细节。
- `setup-and-profiles.md` 保存默认路径、Setup、冷重载和多 Agent Profile 规则。
- `roles-and-approval.md` 保存角色矩阵、状态机和批准边界。
- 保留 `agents/openai.yaml` 作为 Codex UI metadata，并确保它与新 Skill 名称一致。
- Skill 目录不放 README、CHANGELOG、安装说明或发布记录。

### UI 决策门

在删除 `commands/` 前执行两组独立安装实验：

1. 当前 `commands/` 版本，记录 Skill 列表、`/km` 搜索结果和 starter cards。
2. 仅正式 `agentskm` Skill 的候选版本，在全新插件版本和新对话中记录相同结果。

只有确认自然语言触发、Skill 展示和 MCP 调用都通过后，才删除 `commands/`。
不要仅根据当前线程缓存判断 UI 行为。插件级 `defaultPrompt` 是否保留也由该实验决定；
默认倾向是不放三条同名 starter prompts，必要时只保留一条领域级入口。

### 退出条件

- `quick_validate.py` 通过。
- Skill frontmatter 只有 `name` 和 `description`。
- 三份 references 都由 `SKILL.md` 直接引用，且没有重复正文。
- 新对话中自然语言可以触发 Doctor、Search 和 Capture。
- 不依赖生成的 `source-command-*` Skill 完成核心工作流。

## Phase 5：Plugin 最小化与一次安装

目标：插件只承担装配，用户不需要克隆仓库或全局安装 CLI。

### 改动

- 更新 `plugin.json` 指向 `./skills/` 和 `./.mcp.json`。
- 更新 `scripts/build_plugin.py`：
  - 要求 manifest、MCP 配置、正式 Skill 和 UI metadata；
  - 禁止 `tools/`、`adapters/`、Vault、config、缓存和凭证；
  - `commands/` 是否禁止由 Phase 4 UI 决策门决定；
  - 不再强制插件根 README。
- `.mcp.json` 继续使用精确 PyPI pin。
- 增加一项安装前置检查：宿主必须能找到 `uvx`。
- MCP 无法启动时，安装文档明确区分：
  - Plugin 已安装；
  - Skill 已发现；
  - uvx 缺失或 PyPI 获取失败；
  - MCP 启动或 Vault Setup 失败。

### 退出条件

- Plugin 安装包不含 Python 运行时源码。
- 新用户只执行 Marketplace add 和 Plugin add。
- 首次新对话由 uvx 获取运行时并暴露 MCP tools。
- 终端没有全局 `agentskm` 命令也不影响插件使用。

## Phase 6：跨 Agent 文档收敛

目标：将 Codex Plugin 与通用 MCP 分发边界写清楚。

### 改动

- Codex：Marketplace Plugin 安装。
- Hermes、Claude、Cursor：通过各自 MCP 配置调用同一 PyPI Runtime。
- 所有用户文档默认使用：

```text
uvx --from agentskm-toolkit==<version> agentskm mcp ...
```

- 源码路径只出现在开发文档，不出现在用户安装指南。
- 明确不存在跨所有 Agent 的统一 Plugin 协议；通用层是 CLI/MCP 包，Plugin 是宿主适配。
- 删除或标记过期的环境变量和旧源码启动说明。

### 退出条件

- 新机器接入文档不要求克隆 Toolkit。
- 每个 Agent 文档明确 Profile、host、默认角色和共享 Vault 配置。
- 文档命令在临时环境中实际执行通过。

## Phase 7：0.5.0 发布

目标：先发布已验证运行时，再让稳定 Marketplace 指向它。

### 发布顺序

1. 完成源码、wheel、uvx、MCP、Skill 和 Plugin 候选验收。
2. 使用 TestPyPI 验证 `0.5.0rc1` 或等价候选版本。
3. 冻结 `0.5.0` 代码和版本字段。
4. 发布 PyPI `agentskm-toolkit==0.5.0`。
5. 验证生产 PyPI 的 CLI、MCP 和干净 Setup 链路。
6. 将插件 `.mcp.json` pin 切到 `0.5.0`。
7. 发布/更新 Plugin `0.5.0` 和稳定 Marketplace ref。
8. 从全新 Marketplace 安装执行最终验收。

稳定 Marketplace 在 PyPI `0.5.0` 可安装之前，不得暴露指向该版本的 `.mcp.json`。

### 退出条件

- 以下版本全部为 `0.5.0`：
  - PyPI metadata
  - CLI `--version`
  - MCP `serverInfo.version`
  - Plugin manifest
  - Plugin MCP pin
- GitHub Release、PyPI 和 Marketplace 对应同一已验证源码。

## 7. 文件级改动清单

| 文件/目录 | 动作 | 阶段 |
|---|---|---|
| `.github/workflows/ci.yml` | 新增 PR CI | 0 |
| `scripts/check_versions.py` | 新增版本契约检查 | 0 |
| `tests/acceptance/test_km_workflow.py` | 改为优先验证包入口 | 1–3 |
| `tools/km-cli/` | 删除或变为无业务逻辑兼容包装 | 1 |
| `adapters/mcp/` | 删除或变为无业务逻辑兼容包装 | 1 |
| `src/agentskm_toolkit/cli.py` | 完整帮助和错误契约 | 2 |
| `src/agentskm_toolkit/km.py` | bootstrap 错误与核心契约修复 | 2 |
| `src/agentskm_toolkit/mcp.py` | 薄适配和重连语义 | 3 |
| `plugins/agentskm-toolkit/skills/agentskm/` | 新正式 Skill 与 references | 4 |
| `plugins/agentskm-toolkit/skills/agentskm-capture/` | 迁移后删除 | 4 |
| `plugins/agentskm-toolkit/commands/` | UI 验收通过后删除 | 4 |
| `plugins/agentskm-toolkit/README.md` | 将用户内容移到仓库文档后删除 | 5 |
| `scripts/build_plugin.py` | 校验新的最小插件结构 | 5 |
| `integrations/*` | 统一 PyPI/uvx 用户入口 | 6 |
| `pyproject.toml`、manifest、MCP pin | 统一为 0.5.0 | 7 |

## 8. PR 拆分建议

不要在一个 PR 中同时完成全部改造。推荐：

1. `ci: add pull request and version contract checks`
2. `refactor: make packaged runtime the single source of truth`
3. `fix: expose bootstrap failures and complete CLI help`
4. `refactor(mcp): stabilize role and reconnect contracts`
5. `refactor(skill): adopt one progressive-disclosure AgentsKM skill`
6. `refactor(plugin): remove migration-only files after UI acceptance`
7. `docs: align multi-agent installation with uvx runtime`
8. `release: prepare agentskm-toolkit 0.5.0`

每个 PR 必须能独立通过 CI，并且不能修改真实 Vault 或用户配置。

## 9. 验收矩阵

| 场景 | 必须验证 |
|---|---|
| 源码 | CLI 帮助、Setup、角色、完整候选流程 |
| wheel | 安装、版本、CLI、MCP initialize/tools/list |
| uvx wheel | 隔离启动、默认 Vault、Inbox 写入 |
| TestPyPI | metadata、安装、升级、MCP 冷启动 |
| PyPI | 生产索引安装和版本 pin |
| Codex Plugin | Marketplace 安装、Skill 发现、MCP tools、Doctor |
| contributor | search/propose/respond 可用，review/promote 不可用 |
| reviewer | review/dashboard 可用，promote/merge 不可用 |
| compiler | approved 后 promote/merge 可用 |
| 多 Agent | 两个 Profile 共享 Vault，来源字段正确，权限独立 |
| 安全 | secret、路径遍历、角色覆盖、未批准毕业全部拒绝 |
| 数据保护 | 测试只写临时 Vault，不触碰用户 config/Vault |

## 10. 回退策略

- 所有 0.5.0 工作在新分支进行，建议：`feat/0.5-plugin-convergence`。
- 保留当前 `0.4.5` Plugin 和 PyPI `0.4.4` 作为已知可用基线。
- 每个阶段使用独立 PR，允许逐阶段 revert。
- 在稳定 Marketplace 切换前完成全部干净安装验收。
- 发生插件问题时，将 Marketplace ref 恢复到 0.4.5 对应提交并重新安装。
- 发生运行时问题时，将 `.mcp.json` pin 恢复到 `agentskm-toolkit==0.4.4`。
- 回退不得删除 `%USERPROFILE%/.agentskm/config.json` 或用户 Vault。
- 0.5.0 如需修改 Vault schema，必须另建迁移、备份和回退设计；本计划默认不修改 schema。

## 11. 完成定义

满足以下全部条件后，0.5.0 才视为完成：

- [x] PR CI、版本契约和仓库纯度检查通过。
- [x] `src/agentskm_toolkit` 是唯一业务实现。
- [x] CLI 帮助、JSON 错误和 bootstrap 恢复可独立使用。
- [x] MCP 只保留结构化适配逻辑。
- [x] 一个正式 `agentskm` Skill 通过渐进式披露覆盖完整领域。
- [x] 不依赖 `source-command-*` 完成核心工作流。
- [x] 插件目录不含运行时源码、Vault、配置或无关文档。
- [x] 所有跨 Agent 用户文档使用已发布包入口。
- [x] TestPyPI、PyPI、Marketplace 干净安装链路均通过。
- [x] Plugin、PyPI、CLI、MCP 和 pin 版本一致为 `0.5.0`。
- [x] contributor、reviewer、compiler 权限矩阵通过验收。
- [x] 真实用户 Vault 和配置未被测试或发布流程修改。
