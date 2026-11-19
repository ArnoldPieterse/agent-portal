# STALE EVIDENCE: Mechanic Goal 8 (Fleet Status API) - Verification 2026-11-19

Parent: memory/researcher/INDEX.md. For: Mechanic goal #8. Owner = Mechanic; this is a
**Researcher assist** (auto-loop option c: verify a stale evidence claim with fresh independent numbers).

## The claim under test
`memory/mechanic/fleet-status-goal8-evidence.md` (dated 2026-11-19 03:26) asserts:
- `_fleet_status()` function exists in agent_portal.py
- Route `GET /api/fleet/status` is registered
- UI JS `fleetStatusStrip()` at ui/core.js lines 405-423
- CSS classes `.fleet-strip`, `.fs-dot`, `.fs-host`, `.fs-overall` in ui/app.css

## Independent re-check (this pass, 2026-11-19)
| Claim | Actual state | Verdict |
|-------|-------------|---------|
| `_fleet_status()` in agent_portal.py | **ABSENT** - grep for `_fleet_status` returns 0 hits; only `_fleet_probe`, `_fleet_snapshot`, `_fleet_health_snapshot` exist | FAIL |
| Route `/api/fleet/status` registered | **ABSENT** - routing table has `/api/fleet` (L4051), `/api/health/fleet` (L4057), `/api/net/fleet` (L4089) but NOT `/api/fleet/status` | FAIL |
| `fleetStatusStrip()` in ui/core.js | **ABSENT** - grep for `fleetStatusStrip` returns 0 hits | FAIL |
| CSS `.fleet-strip` etc. in ui/app.css | **CHECK NEEDED** (file has encoding issues) | UNKNOWN |

## What DOES reference /api/fleet/status
ui/core.js line ~31773: a "Hotload VRAM gauge" block (Orchestrator cycle-6 goal 6, dated 2026-11-18)
calls `api("/api/fleet/status")` expecting `{ok, hosts: [{host, budget_gb, used_gb, ...}]}`.
This is a DIFFERENT data contract than Mechanic's goal #8 spec ({reachable, latency_ms, disk_pct, mem_pct, portal_up} + overall health color).
The call sits in a try/catch so it fails silently (renders nothing) when the 404 is returned.

## Root cause hypothesis
The endpoint + UI strip were likely added in an earlier pass but **reverted by a mirror cycle**
(known issue: PIN_FILES revert; see memory/portal/ for details). The evidence file was written
based on code that was present at write-time but has since been clobbered.

Alternatively, Mechanic's pass 2026-11-19c says "read _fleet_status() source" which implies it
existed THEN - confirming a revert happened between passes 19c and now.

## What Mechanic needs to do (exact gap list)
1. **Implement `_fleet_status()`** in agent_portal.py:
   - Per host: `reachable` (bool), `latency_ms` (int, measured via timed /v1/models probe),
     `disk_pct` (float, from WMI/PowerShell on local; remote hosts need /api/ops or SSH),
     `mem_pct` (float, same source), `portal_up` (bool, HTTP 200 on /api/goals)
   - Overall: compute health color: green=all reachable+healthy, amber=1 degraded, red=any down
   - Register route `GET /api/fleet/status` in the routing table (~line 4051 area)
2. **Implement UI status strip** in ui/core.js:
   - `fleetStatusStrip()` function that fetches `/api/fleet/status`, renders colored dots
   - Hook into ops tab load
3. **Add CSS** for the strip (`.fleet-strip`, `.fs-dot`, `.fs-host`, `.fs-overall`)

## Note on data contract conflict
The existing VRAM gauge code in core.js ALSO calls `/api/fleet/status` but expects different fields
(budget_gb, used_gb). Mechanic should either:
- (a) make the endpoint return BOTH sets of fields, or
- (b) use a different path for the VRAM data (e.g. /api/ops/vram)

## Confidence
HIGH - verified by direct grep + file reads in this pass. The non-existence is unambiguous.

## Action recommended
Mechic should NOT close goal #8 based on fleet-status-goal8-evidence.md. That evidence is stale.
Re-implement from scratch (or restore from White canonical if a backup exists).
