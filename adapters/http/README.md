# AgentsKM HTTP Adapter

Thin localhost HTTP adapter over `tools/km-cli/km.py --json`.

Start:

```powershell
python adapters/http/km_http.py --host 127.0.0.1 --port 8765
```

Endpoints:

| Method | Path | Maps to |
|---|---|---|
| `GET` | `/health` | Adapter health |
| `GET` | `/status` | `km status --json` |
| `GET` | `/pending` | `km pending --json` |
| `GET` | `/search?q=...&limit=10` | `km search ... --json` |
| `GET` | `/validate` | `km validate --json` |
| `GET` | `/lint` | `km lint --json` |
| `POST` | `/propose` | `km propose ... --json` |
| `POST` | `/promote` | `km promote ... --json` |

The adapter must remain thin. All validation, role boundaries, locks, transactions, and promotion rules live in the KM CLI.

