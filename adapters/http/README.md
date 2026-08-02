# AgentsKM HTTP Adapter

Optional loopback-only adapter over the KM CLI. A Bearer Token is mandatory for
all endpoints except `/health`.

```powershell
$env:AGENTSKM_HTTP_TOKEN="generate-a-local-secret"
python adapters/http/km_http.py --host 127.0.0.1 --port 8765 --profile hermes-agent
```

Read endpoints: `/health`, `/status`, `/pending`, `/reminders`, `/search`,
`/validate`, and `/lint`.

Write endpoints: `/propose`, `/review`, `/promote`, and `/merge`. Send:

```text
Authorization: Bearer <AGENTSKM_HTTP_TOKEN>
```

Do not expose this adapter to a public network.
