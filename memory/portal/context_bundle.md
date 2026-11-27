# context_bundle.py - the gettable context + API-inputs file (2026-11-27, user directive)
<!-- parent: memory/portal/INDEX.md | owner: Archivist | code: L-module leaf -->
"Build the context and api inputs as a gettable file from any of the hosts, and they can also
request data." - this module + bundle_host.py implement exactly that.

## What it is
`memory/portal/context_bundle.py::build()` assembles ONE self-describing JSON document
(`context-bundle.json`, project root) with four sections:
- **context** - M-CODE map (parsed from MEMORY.md), per-module pointer indexes, hot notes,
  live goal state (open titles per lane via goal_ledger.parse_agent_file), round topic.
- **api_inputs** - the documented route table (memory/portal/api-index.md, SSOT) PLUS POST body
  specs DERIVED FROM THE LIVE SOURCE (body.get("key") per branch in agent_portal.py) PLUS the GEV
  MCP tool schemas (the real-world data API). This is "API inputs" = what each endpoint accepts.
- **fleet** - all 4 hosts with studio URLs + bundle URLs (:8199 each), models, GEV status.
- **how_to_use** - exact GET/POST recipes so any client or agent can work from the file alone.

## How it's gettable from ANY host (three identical surfaces)
1. `GET http://127.0.0.1:8099/api/context-bundle` - White portal hub (regenerates if stale >5 min).
2. `GET http://<host>:8199/context-bundle.json` - bundle_host.py on every host (stdlib-only HTTP
   server, schtasks PortalBundle; rebuilds its local copy if >30 min old).
3. `C:\Projects\AgentPortal\context-bundle.json` / the sandbox `_default` dir on each remote -
   kept fresh by the 5-min SMB mirror (INTERNAL_ONLY in memory_mirror.py).

## Data requests ("they can also request data")
- Hub: `POST http://127.0.0.1:8099/api/data-request` -> `_hub_data_request()` in agent_portal.py
  (serves HERE + Studio sandbox; byte-capped; audited to memory/ops/data-requests.jsonl).
- Any host: `POST http://<host>:8199/data-request` -> bundle_host.py (that host's own mirror copy).
- Wire format both sides: `{from?, wants:[{"path": rel}|{"query": text}], max_bytes?}` - one dead
  want never kills the batch; traversal + dotfiles rejected.

## Lifecycle
Portal `_world_watchdog` thread (boot, agent_portal.py) rebuilds the bundle every 10 min so the
mirror always has fresh bytes to push; same thread takes a GEV world snapshot every 30 min
(memory/world/gev_snapshot.py). Both best-effort - neither can take the portal down.
