# Codex Plugin UI Migration Gate

The 0.5.0 candidate uses one formal `agentskm` Skill. The three files under
`commands/` remain only as a controlled compatibility baseline because Codex
may migrate them into internal `source-command-*` Skills. They are not a
separate runtime and do not guarantee slash-menu entries.

## Preconditions

- Publish `agentskm-toolkit==0.5.0` to production PyPI before testing the
  unchanged plugin pin. A TestPyPI-only experiment must use a separate
  temporary MCP config that explicitly selects the TestPyPI index.
- Push the candidate plugin to a dedicated remote branch.
- Use a fresh plugin version/cache key and a new Codex conversation for each
  experiment.
- Do not modify the real user Vault during UI inspection.

## Experiment A: Compatibility Baseline

Install the candidate with `commands/` present. Record:

- the plugin version and source ref;
- visible Skill names and descriptions;
- generated `source-command-*` entries in the plugin cache;
- `/km` search/menu results;
- starter cards;
- natural-language Doctor, Search, and Capture behavior;
- the MCP tool list and `km_doctor` result.

## Experiment B: Formal Skill Only

Create a separate commit that removes `commands/`, increments the plugin
cache/version, and changes nothing else. Reinstall from that ref in a new
conversation and record the same observations.

## Decision

Delete `commands/` from the release only when Experiment B passes all of:

- one clear `agentskm` Skill is visible;
- no `source-command-*` entries are generated;
- natural-language Doctor, Search, and Capture requests trigger the Skill;
- MCP calls and role boundaries remain correct;
- the UI does not depend on slash entries for the core workflow.

If the formal Skill is not discovered, keep `commands/` temporarily and file
the exact host version/cache evidence. Do not reintroduce multiple plugin-level
starter prompts as a workaround.
