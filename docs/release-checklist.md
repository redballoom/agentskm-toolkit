# AgentsKM Toolkit Release Checklist

This checklist keeps package release separate from plugin defaults and Vault
data. Never publish user Vault files or local config.

## Accounts And Trusted Publishing

- PyPI account exists and 2FA is enabled.
- TestPyPI account exists and 2FA is enabled.
- PyPI pending publisher:
  - Project name: `agentskm-toolkit`
  - Owner/repository: `redballoom/agentskm-toolkit`
  - Workflow: `publish.yml`
  - Environment: `pypi`
- TestPyPI pending publisher:
  - Project name: `agentskm-toolkit`
  - Owner/repository: `redballoom/agentskm-toolkit`
  - Workflow: `publish.yml`
  - Environment: `testpypi`

## Before TestPyPI

- Confirm the release version in `pyproject.toml`.
- Run `python scripts/check_versions.py` and confirm package, CLI, MCP, plugin,
  and runtime pin all match.
- Run `python scripts/check_repo_purity.py` and inspect the staged diff for
  credentials or user data.
- Run local acceptance:

```powershell
python scripts\build_plugin.py --check
python tests\acceptance\test_km_workflow.py
python -m build
uvx --from (Get-ChildItem .\dist\agentskm_toolkit-*.whl | Select-Object -First 1).FullName agentskm --version
```

- Push the release branch to GitHub.
- Confirm Git source install works:

```powershell
uvx --from "git+https://github.com/redballoom/agentskm-toolkit.git@feat/0.5-plugin-convergence" agentskm --version
```

## Publish To TestPyPI

- Open GitHub Actions.
- Run workflow: `publish`.
- Select target: `testpypi`.
- Confirm the `testpypi` environment approval if configured.
- Verify installation from TestPyPI:

```powershell
uvx --isolated --no-cache --default-index https://test.pypi.org/simple/ --from agentskm-toolkit==0.5.0 agentskm --version
```

## Before Production PyPI

- Merge the tested branch to `main`.
- Create a GitHub release or manually run the workflow with target `pypi`.
- Confirm the `pypi` environment approval if configured.
- Verify production install:

```powershell
uvx --from agentskm-toolkit==0.5.0 agentskm --version
```

## Codex Plugin Runtime

- Pin the plugin MCP template to the verified production release:

```json
{
  "command": "uvx",
  "args": ["--from", "agentskm-toolkit==0.5.0", "agentskm", "mcp"]
}
```

- Confirm the plugin contains no bundled `tools/` or `adapters/` runtime copy.
- Run `python scripts/build_plugin.py --check` and plugin schema validation.
- Run plugin install and setup acceptance in Codex and at least one contributor
  host.
- Do not move the stable Marketplace ref to the 0.5.0 plugin before production
  PyPI can install the exact pin.
