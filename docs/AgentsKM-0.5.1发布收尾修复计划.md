# AgentsKM 0.5.1 发布收尾修复计划

> 状态：本地验收完成（待推送、PR 与 TestPyPI）
>
> 日期：2026-08-04
>
> 基线：`origin/main` / `f824e0c`
>
> 工作分支：`codex/0.5.1-release-closure`

## 1. 目标

0.5.1 是 0.5.0 的收尾修复版本，不改变 Vault schema、Profile 权限模型或
CLI/MCP/Skill 的职责边界。它只修复正式安装、发布自动化和 MCP 参数契约中
已经通过真实验收复现的问题。

## 2. 已确认问题

1. 仓库根目录保存 Marketplace manifest，使用
   `--sparse plugins/agentskm-toolkit` 会导致 Codex 找不到 manifest。
2. `release.published` 会再次触发 PyPI 发布，但 `pypi` Environment 不允许 tag
   部署，造成 GitHub Release 后出现失败运行。
3. `km_propose_capture.type` 的 MCP Schema 接受任意字符串，CLI 实际只接受
   `comparison`、`concept`、`entity`、`guide`、`note`、`query`、`summary`。
4. 0.5.0 执行计划和发布文档尚未更新为最终状态。

## 3. 实施范围

- Marketplace 安装命令固定为：

  ```powershell
  codex plugin marketplace add redballoom/agentskm-toolkit --ref main
  codex plugin add agentskm-toolkit@agentskm-official
  ```

- `publish.yml` 只允许手动 `workflow_dispatch`：
  - feature/release 分支可发布 TestPyPI；
  - 只有 `main` 可选择正式 PyPI；
  - GitHub Release 在正式 PyPI 验证后创建，不重复发布包。
- MCP `type` Schema 直接复用 CLI 的 `WIKI_DIRS` 合法值，并由 acceptance 测试
  固定枚举契约。
- package、CLI、MCP、plugin manifest 和 PyPI pin 统一为 `0.5.1`。
- 不写入或迁移用户 config、Vault、Inbox 或 Wiki。

## 4. 发布顺序

1. 本地运行纯度、版本、插件构建和完整 acceptance。
2. 推送修复分支并通过 PR CI。
3. 从修复分支手动发布 TestPyPI 0.5.1，并执行隔离 CLI/MCP/角色测试。
4. 合并到 `main`。
5. 从 `main` 手动发布正式 PyPI 0.5.1。
6. 验证正式 PyPI 后创建 `v0.5.1` tag 和 GitHub Release。
7. 从 GitHub `main` 干净安装 Codex 插件，并在新会话运行 `km_doctor`、Skill
   触发和 Capture dry-run。
8. 在 Hermes contributor Profile 做一次真实 MCP 复测。
9. 经用户单独授权后清理旧远端分支与本机 Marketplace staging。

## 5. 验收标准

- [x] `python scripts/check_repo_purity.py` 通过。
- [x] `python scripts/check_versions.py` 报告所有发行面为 0.5.1。
- [x] `python scripts/build_plugin.py --check` 通过。
- [x] `python tests/acceptance/test_km_workflow.py` 通过。
- [x] MCP Capture Schema 的 `type.enum` 与 CLI 合法类型一致。
- [x] 仓库活动安装文档不再要求 `--sparse`。
- [x] GitHub Release 不再触发第二次 PyPI 发布。
- [ ] TestPyPI 与正式 PyPI 0.5.1 均可隔离安装。
- [ ] 官方插件 Doctor 返回 0.5.1、正确 Profile/role 和 `ready`。
- [ ] Capture dry-run 不修改真实 Vault。
- [ ] Hermes contributor 的工具可见性和权限拒绝复测通过。

## 6. 数据连续性观察项

2026-08-04 验收时，当前配置指向的默认 Vault 只有 `README.md` 与
`index.md`，Inbox/Wiki 均为空。0.5.1 开发和测试不得修改该 Vault；旧数据是否
需要恢复由用户另行确认，不与代码发布混合处理。

## 7. 当前执行记录

- 已从 `origin/main` 创建本地分支 `codex/0.5.1-release-closure`。
- 已移除 Release 自动发布入口，正式 PyPI 保留 `main` 手动发布。
- 已为 Capture `type` 增加 MCP 枚举并补 acceptance 断言。
- 已将发行版本和插件 runtime pin 更新为 0.5.1。
- 已修正 Marketplace 安装说明，明确当前仓库布局不能使用 `--sparse`。
- 本地完整 acceptance 已通过，测试只使用临时 config/Vault。
- 已构建 0.5.1 wheel/sdist，Twine 元数据校验均通过。
- 已从本地 wheel 启动 CLI 和 contributor MCP；版本、11 工具、Doctor 与
  Capture Schema 均符合预期。
