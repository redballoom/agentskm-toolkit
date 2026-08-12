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
uvx --from "git+https://github.com/redballoom/agentskm-toolkit.git@<release-branch>" agentskm --version
```

## Publish To TestPyPI

- Open GitHub Actions.
- Run workflow: `publish`.
- Select target: `testpypi`.
- Confirm the `testpypi` environment approval if configured.
- Verify installation from TestPyPI:

```powershell
uvx --isolated --no-cache --default-index https://test.pypi.org/simple/ --from agentskm-toolkit==0.5.3 agentskm --version
```

## Before Production PyPI

- Merge the tested branch to `main`.
- Manually run the `publish` workflow with target `pypi` from `main`.
- Confirm the `pypi` environment approval if configured.
- Create the GitHub Release only after PyPI verification. Publishing a Release
  does not run the package workflow again.
- Verify production install:

```powershell
uvx --from agentskm-toolkit==0.5.3 agentskm --version
```

## Codex Plugin Runtime

- Pin the plugin MCP template to the verified production release:

```json
{
  "command": "uvx",
  "args": ["--from", "agentskm-toolkit==0.5.3", "agentskm", "mcp"]
}
```

- Confirm the plugin contains no bundled `tools/` or `adapters/` runtime copy.
- Run `python scripts/build_plugin.py --check` and plugin schema validation.
- Run plugin install and setup acceptance in Codex and at least one contributor
  host.
- Do not move the stable Marketplace ref to the 0.5.3 plugin before production
  PyPI can install the exact pin.

## Codex Marketplace Install

The repository root contains the Marketplace manifest. Install without a
sparse path:

```powershell
codex plugin marketplace add redballoom/agentskm-toolkit --ref main
codex plugin add agentskm-toolkit@agentskm-official
```

## Local Codex Pre-Release Test

Before the exact package version is available on PyPI, build an ignored local
marketplace whose MCP entry points at the current wheel:

```powershell
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
python scripts\build_local_codex_marketplace.py
codex plugin marketplace add .\build\local-codex-marketplace
codex plugin add agentskm-toolkit@agentskm-local
```

Fully restart Codex and start a new conversation before testing Skill triggers
or the role-filtered MCP tool list. The generated marketplace lives under
ignored `build/`; never publish its machine-specific wheel path.
