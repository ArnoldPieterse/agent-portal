# Evidence: Goal 9 — Provenance API Endpoint (2026-11-20)

**What was done:** Wired `/api/memory/provenance?file=X` into `agent_portal.py` (inserted after `/api/memory/file` handler, ~line 4159).

## Endpoint behaviour
| Call | Returns |
|------|---------|
| `GET /api/memory/provenance` | Summary: total_files, agent_coverage_pct, trigger_coverage_pct |
| `GET /api/memory/provenance?file=memory/goals/archivist.md` | `{"ok":true,"record":{"file":...,"agent":...,"created":...,"modified":...,"trigger":...,"source":...}}` |
| `GET /api/memory/provenance?file=<unknown>` | 404 + error message |

## Verification
- Syntax check: `py_compile.compile('agent_portal.py', doraise=True)` → PASS (one pre-existing SyntaxWarning, unrelated)
- Live HTTP test blocked by sandbox firewall (WinError 10013); endpoint will be live on next portal restart/mirror cycle
- Data source: `memory/archivist/provenance-data.json` (6464 records, generated 2026-11-20T10:58)

## Remaining for full goal closure
- Portal restart to activate endpoint (Mechanic/Orchestrator action)
- Post-restart live test confirming 200 + correct record