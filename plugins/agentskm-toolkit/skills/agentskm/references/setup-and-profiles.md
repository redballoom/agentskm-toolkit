# Setup And Profiles

## Default Bootstrap

On first MCP startup, AgentsKM attempts to create:

- `%USERPROFILE%/.agentskm/config.json`;
- the Profile requested by the host;
- `%USERPROFILE%/Documents/AgentsKM/vault` with an empty Vault layout.

The config file is the only source for Profile roles and Vault paths. Multiple
Agents share one Vault by pointing their Profiles at the same configured Vault.
Do not use environment variables for config, Profile, role, or Vault selection.

## Diagnosis

Call `km_setup_status`, then `km_doctor`. Report the toolkit version, config
path, Profile, host, role, Vault name/path, failed checks, and `next_action`.
If setup is ready, continue without asking the user to configure it again.

## Failed Bootstrap

Automatic setup may refuse an invalid/legacy config, a conflicting Profile, or
a non-empty directory that is not an AgentsKM Vault. Preserve and explain the
reported `bootstrap_error`; do not replace it with a generic startup message.

Call `km_setup_instructions` and show its exact `cli_command`. Run that command
only with normal task authorization. Never edit `config.json` directly. A new
compiler Profile requires explicit user confirmation and the CLI's
`--confirm-compiler` guard.

## Reconnection

MCP tool visibility is fixed when the connection starts. Setup, Profile role
changes, and runtime updates can return `reconnect_required: true`. Reconnect
the MCP server when supported; otherwise start a new conversation. Vault path
changes with the same role are re-read by CLI operations, but reconnecting is
still the clearest cold-start diagnostic boundary.
