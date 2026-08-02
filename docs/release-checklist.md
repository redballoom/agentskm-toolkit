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
- Confirm the CLI and MCP versions match the package version.
- Run local acceptance:

```powershell
python tests\acceptance\test_km_workflow.py
uv build
uvx --from (Get-ChildItem .\dist\agentskm_toolkit-*.whl | Select-Object -First 1).FullName agentskm --version
```

- Push the release branch to GitHub.
- Confirm Git source install works:

```powershell
uvx --from "git+https://github.com/redballoom/agentskm-toolkit.git@feat/uvx-productization" agentskm --version
```

## Publish To TestPyPI

- Open GitHub Actions.
- Run workflow: `publish`.
- Select target: `testpypi`.
- Confirm the `testpypi` environment approval if configured.
- Verify installation from TestPyPI:

```powershell
uvx --index-url https://test.pypi.org/simple/ --from agentskm-toolkit agentskm --version
```

## Before Production PyPI

- Merge the tested branch to `main`.
- Create a GitHub release or manually run the workflow with target `pypi`.
- Confirm the `pypi` environment approval if configured.
- Verify production install:

```powershell
uvx --from agentskm-toolkit agentskm --version
```

## After Production PyPI

- Switch the plugin MCP template from bundled source runtime to:

```json
{
  "command": "uvx",
  "args": ["--from", "agentskm-toolkit", "agentskm", "mcp"]
}
```

- Run plugin install and setup acceptance in Codex and at least one contributor
  host.
