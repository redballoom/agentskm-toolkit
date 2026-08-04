# MCP Compatibility Launcher

`km_mcp.py` is a source-checkout compatibility launcher. It imports the MCP
server from `src/agentskm_toolkit` and contains no tool or workflow logic.

Product integrations must use the packaged entrypoint:

```powershell
uvx --from agentskm-toolkit==0.5.2 agentskm mcp --profile hermes-agent --host hermes --bootstrap-role contributor
```

For an editable development install, use `agentskm mcp ...`. The MCP server
adapts CLI JSON operations into structured tools and fixes role-based tool
visibility for the lifetime of a connection. Setup or role changes require a
reconnect.
