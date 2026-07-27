# AgentsKM MCP Adapter

Thin MCP stdio adapter over `tools/km-cli/km.py --json`.

For split installs, set `AGENTSKM_DATA_ROOT` to the local knowledge vault path
before starting the adapter:

```powershell
$env:AGENTSKM_DATA_ROOT="D:\Human-Agent_Collab\AGENTSKM\agentskm-vault"
```

Start command:

```powershell
python adapters/mcp/km_mcp.py
```

Example MCP server configuration:

```json
{
  "mcpServers": {
    "agentskm": {
      "command": "python",
      "args": ["D:/AgentsKM/adapters/mcp/km_mcp.py"]
    }
  }
}
```

Exposed tools:

| Tool | Maps to |
|---|---|
| `km_status` | `km status --json` |
| `km_pending` | `km pending --json` |
| `km_search` | `km search ... --json` |
| `km_validate` | `km validate --json` |
| `km_lint` | `km lint --json` |
| `km_propose_capture` | `km propose ... --json` |
| `km_promote_candidate` | `km promote ... --json` |
| `km_dashboard` | `km dashboard --json` |

The adapter only translates MCP tool calls into CLI invocations. All validation, locks, transactions, promotion rules, and audit writes remain in the KM CLI.
