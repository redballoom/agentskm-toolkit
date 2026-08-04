# AgentsKM 维护与发布指南

本指南面向 Toolkit 仓库维护者。最终用户不需要执行这里的源码命令。

## 1. 源码边界

```text
src/agentskm_toolkit/          唯一运行时源码
plugins/agentskm-toolkit/     轻量 Codex 插件：Skill、commands、MCP 注册
.agents/plugins/              Marketplace 根清单
integrations/                 其他宿主的接入说明
tests/acceptance/             临时 Vault 端到端验收
```

`tools/km-cli` 和 `adapters/mcp` 仅是 0.5.x 源码工作流兼容启动器，不得增加业务逻辑。
插件包不得捆绑 runtime、用户配置、Vault、凭证或测试数据。

## 2. 开发环境

```powershell
git clone https://github.com/redballoom/agentskm-toolkit.git
cd agentskm-toolkit
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Linux/macOS 使用对应的虚拟环境激活命令。开发和验收不得指向真实用户 Vault。

## 3. 提交前验证

```powershell
python scripts\check_repo_purity.py
python scripts\check_versions.py
python scripts\build_plugin.py --check
python tests\acceptance\test_km_workflow.py
```

这些检查分别验证仓库纯度、各处版本与 PyPI pin 一致性、插件结构和完整临时 Vault
工作流。还应人工检查 staged diff，确认没有配置文件、知识内容、Token、绝对测试路径
或个人数据。

## 4. 本地分发验收

```powershell
python -m build
$wheel = (Get-ChildItem .\dist\agentskm_toolkit-*.whl | Select-Object -First 1).FullName
uvx --isolated --no-cache --from $wheel agentskm --version
$acceptanceRoot = Join-Path $env:TEMP "agentskm-wheel-acceptance"
$acceptanceConfig = Join-Path $acceptanceRoot "config.json"
$acceptanceVault = Join-Path $acceptanceRoot "vault"
uvx --isolated --no-cache --from $wheel agentskm setup `
  --config $acceptanceConfig --profile codex --host codex `
  --role compiler --confirm-compiler --vault $acceptanceVault --json
uvx --isolated --no-cache --from $wheel agentskm doctor `
  --config $acceptanceConfig --profile codex --json
```

完成后只清理已核对路径的 `$acceptanceRoot`。Doctor 测试必须通过 `--config` 使用临时
配置和 Vault，不能修改维护者的正式知识库。

分支推送后再验证 Git 安装源：

```powershell
uvx --isolated --no-cache `
  --from "git+https://github.com/redballoom/agentskm-toolkit.git@<branch>" `
  agentskm --version
```

## 5. 发布顺序

1. 在发布分支同步 package、CLI、MCP、plugin manifest 和 `.mcp.json` 版本。
2. 完成本地 purity、version、plugin 和 acceptance 检查。
3. 创建 PR，等待 Python 3.10、3.11、3.12 CI 全部通过。
4. 从发布分支手动发布 TestPyPI，并等待索引传播。
5. 使用隔离 `uvx` 验证 TestPyPI 的 CLI、Setup、Doctor、MCP 和权限边界。
6. 合并到 `main`，从 `main` 手动发布正式 PyPI。
7. 验证正式 PyPI 后创建 GitHub Release。
8. 从 GitHub `main` 干净安装 Codex 插件，并在新会话执行 `km_doctor`。
9. 至少使用一个 contributor 宿主完成 Inbox 写入和 compiler 接续验收。

完整发布命令和 Trusted Publishing 条件见
[release-checklist.md](../release-checklist.md)。

## 6. TestPyPI 与 PyPI 验收

TestPyPI：

```powershell
uvx --isolated --no-cache `
  --default-index https://test.pypi.org/simple/ `
  --from agentskm-toolkit==<version> agentskm --version
```

正式 PyPI：

```powershell
uvx --isolated --no-cache --from agentskm-toolkit==<version> agentskm --version
```

工作流成功不等于索引已立即可解析；短暂出现“No solution found”时，先查看发布 Job
和项目页面，再等待索引传播，不要重复发布相同版本。

## 7. 官方 Codex 插件验收

```powershell
codex plugin marketplace upgrade agentskm-official
codex plugin add agentskm-toolkit@agentskm-official
codex plugin list --json
```

若机器上尚未添加 Marketplace：

```powershell
codex plugin marketplace add redballoom/agentskm-toolkit --ref main
codex plugin add agentskm-toolkit@agentskm-official
```

仓库根清单是安装入口，不使用 `--sparse plugins/agentskm-toolkit`。安装后必须开新会话，
检查实际 Toolkit version、Profile、Role、Vault 和工具列表，不能只检查缓存目录名称。

## 8. 版本与兼容策略

- Marketplace `main` 只能引用已在正式 PyPI 可安装的精确版本。
- 不在补丁版本中无提示删除 CLI、MCP tool、Profile 字段或兼容启动器。
- 角色变化需要新的 MCP 连接；不要尝试在连接中动态扩权。
- Git 标签、Release、合并 PR 和正式发布 Actions 记录属于审计历史，应保留。
- 发布完成后删除已合并开发分支，并开启 GitHub 自动删除合并分支。
