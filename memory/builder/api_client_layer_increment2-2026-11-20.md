# Goal #2 API Client Layer - increment 2 (2026-11-20)

## What was done

Wired ALL direct fetch() calls in core.js and uploads.js to apiClient methods.

### api-client.js additions (150L -> 172L, still <500 rule)
- `rawRequest(path, opts)`: returns raw Response without JSON parsing (for streaming endpoints)
- `postChatStream(payload, opts)`: POST /api/chat returning raw Response (supports AbortSignal)
- `runEventsStream(runId, cursor, opts)`: GET /api/run-events returning raw Response
- `fleetDepsGraph()`: GET /api/fleet/dependencies-graph

### core.js wiring (4 fetch calls replaced)
| Line | Before | After |
|------|--------|-------|
| 186 | fetch("/api/chat", {signal, method:POST, ...}) | apiClient.postChatStream(payload, {signal}) |
| 283 | fetch("/api/file?path="+...) | apiClient.getFile(c).catch(()=>null) |
| 430-432 | fetch("/api/fleet/dependencies-graph") + r.ok check + r.json() | apiClient.fleetDepsGraph() |
| 525-526 | fetch("/api/fleet/status") + r.json() | apiClient.fleetStatus() |

### uploads.js wiring (6 fetch calls replaced)
| Line | Before | After |
|------|--------|-------|
| 75-78 | fetch("/api/group-run", POST) + resp.ok check + resp.json() | apiClient.groupRun({text}) |
| 181-182 | fetch("/api/run-events?run=...") + resp.ok check | apiClient.runEventsStream(rid, cursor, {signal}) |
| 332 | await (await fetch("/api/uploads")).json() | apiClient.listUploads() |
| 350 | await (await fetch("/api/goals")).json() | apiClient.getGoals() |
| 373 | fetch("/api/goals/history").then(r=>r.json()) | apiClient.goalsHistory().then(...) |
| 385 | fetch("/api/memory-health").then(r=>r.json()) | apiClient.memoryHealth().then(...) |

### index.html
Added `<script src="ui/api-client.js"></script>` between components.js and core.js (load order).

## Verification (this host, no JS engine)
- Brace balance: api-client.js OK, core.js OK, uploads.js OK
- Static gate: `python memory/builder/gate_api_client.py` -> PASS (172 lines, 17/17 endpoints + 4 new methods)
- Remaining fetch() in core.js: 1 (the `api()` helper definition at line 14, used by 9 call sites for endpoints without typed wrappers yet: /api/models, /api/knowledge-bases, /api/tools, /api/memory, /api/run-state, /api/activity)
- Remaining fetch() in uploads.js: 0

## Error-handling note
For group-run (uploads.js): changed catch to `const em=(e.data&&e.data.error)||String(e)` so the "group run is already in progress" regex still matches ApiError objects.

## REMAINING for full closure
1. Add typed wrappers for remaining 6 endpoints (/api/models, /api/knowledge-bases, /api/tools, /api/memory, /api/run-state, /api/activity) and wire the `api()` helper call sites in core.js to them -> then remove the `api()` helper entirely.
2. Execute node test: `node memory/builder/test_api_client.js` on a node-capable host (sandbox has no node runtime).
3. Live browser smoke test: load portal, send a chat message, verify streaming works via apiClient.postChatStream; verify error boundary cards appear on API failure.
4. index.html pin advancement (script tag addition changes sha12).