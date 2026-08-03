# AgentsKM Toolkit Development Workflow

## Source Of Truth

The only publishable Toolkit source is the standalone Git repository containing
this document.

All CLI, MCP, HTTP adapter, plugin, Skill, integration, packaging, test, and
Toolkit documentation changes must be implemented and committed there.

## Test And Experiment Workspace

A separate Vault-oriented workspace may be used for:

- temporary integration experiments;
- disposable Vault workflow tests;
- design drafts and acceptance fixtures;
- verifying a locally built plugin against realistic knowledge data.

It is not a plugin release source. Toolkit code copied into this workspace is
a test artifact and must not be treated as canonical or pushed as the plugin
repository.

## Required Delivery Sequence

1. Make Toolkit changes in the canonical `agentskm-toolkit` repository.
2. Run `python scripts\build_plugin.py --check` to validate the lightweight plugin.
3. Run `python scripts\check_versions.py` and `python scripts\check_repo_purity.py`.
4. Confirm the plugin MCP version pin matches the intended PyPI release.
5. Run Python syntax checks for changed runtime files.
6. Run `python tests\acceptance\test_km_workflow.py` with a disposable Vault
   fixture.
7. Review `git status` and ensure no Vault knowledge, user configuration,
   credentials, caches, or test output entered the repository.
8. Commit and push only after the repository-level checks pass.

## Repository Purity Rules

Do not commit:

- live `000_Inbox/`, `wiki/`, `raw/`, `.obsidian/`, or `.km/` data;
- `%USERPROFILE%\.agentskm\config.json`;
- absolute machine-specific Vault paths;
- credentials, tokens, conversation transcripts, or customer data;
- generated caches, locks, transactions, or temporary acceptance Vaults.

Acceptance tests must copy their source fixture to a temporary directory before
performing writes.
