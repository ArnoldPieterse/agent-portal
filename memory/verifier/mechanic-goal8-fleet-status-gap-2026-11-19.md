# Mechanic Goal 8 - Fleet Status API: Gap Analysis (2026-11-19)

**Status: GAP CONFIRMED - endpoint exists but incomplete vs spec**

## What the goal requires (`/api/fleet/status`)
Per-host: {reachable, latency_ms, disk_pct, mem_pct, portal_up}
Plus: last check time, overall fleet health (green/amber/red)
UI: status strip at top of ops tab.

## What actually exists

### Endpoint: `/api/health/fleet` (NOT `/api/fleet/status`)
Located at agent_portal.py L991-1070 (`_fleet_health_snapshot()`).
Docstring says "Mechanic cycle-2 goal 8" - this is a PARTIAL implementation from an earlier cycle.

**Fields returned per host:**
| Field | Present? | Notes |
|-------|----------|-------|
| probe.status (reachable proxy) | YES | From probe-evidence.jsonl; values: "ok"/"fail"/absent |
| latency_ms | NO | Not collected or returned |
| disk_pct | NO | Not collected or returned |
| mem_pct | NO | Not collected or returned |
| portal_up | NO | Not collected or returned |
| last_sync / sync_age_s | YES | From memory_mirror.log |

**Top-level fields:**
| Field | Present? |
|-------|----------|
| generated (timestamp) | YES |
| last_probe_line | YES (from fleet_probe.log) |
| git_head / git_goals freshness | YES |
| overall_health (green/amber/red) | NO |

### UI status strip
- NOT present. No ops-tab status strip found in ui/*.js.

## Gap Summary (what needs to be built)
1. **Rename or alias** `/api/health/fleet` -> `/api/fleet/status` (or add both)
2. **Add per-host fields**: latency_ms, disk_pct, mem_pct, portal_up
   - `reachable`: already derivable from probe.status (map "ok"->true)
   - `latency_ms`: needs timing around the probe call (or read from net_probe.state.json)
   - `disk_pct` / `mem_pct`: needs SMB/SSH remote query OR local-only for White
   - `portal_up`: check if agent_portal.py PID is alive on that host
3. **Add overall_health**: compute green/amber/red from host statuses
4. **Add UI status strip**: small colored bar at top of ops tab reading the endpoint

## Existing building blocks to reuse
- `memory/mechanic/net_probe.py` - already tracks latency + reachability per host (state in net_probe.state.json)
- `memory/mechanic/health_check.py` - already checks disk <80%, mem <90% locally
- `_fleet_probe()` at L843 - existing per-host liveness probe (Studio /v1/models)
- `/api/net/fleet` endpoint - calls `_netcmd_mod().fleet_probe()` for outbound probes

## Verdict
Goal 8 is NOT closable as-is. The endpoint exists but covers ~40% of the spec. 
The missing fields (disk_pct, mem_pct, portal_up, latency_ms, overall_health) are the hard part 
because they require either remote execution or reading from existing probe state files.

**Recommended approach**: Read from net_probe.state.json for latency/reachable, 
from health_check.py's last run output for disk/mem, and add a simple PID check for portal_up.
All local file reads - no new outbound calls needed.

---
Verifier: evidence-first gap analysis; no code changes made; all claims verified by reading agent_portal.py source.
