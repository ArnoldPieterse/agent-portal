# Goal #7 - Fleet Health Dashboard v2: Collector + Endpoint Extension Built

Date: 2026-11-18
Agent: Mechanic (on Red sandbox)
Status: CODE BUILT + LOCAL TEST PASS; pending fleet-wide validation

## What was built
1. **`memory/ops/fleet_stats_collect.py`** - per-host stats collector:
   - disk_pct: via shutil.disk_usage (C:\) - returns None in sandbox (Access denied), works on real hosts
   - mem_pct: via wmic -> ctypes.GlobalMemoryStatusEx fallback - CONFIRMED WORKING (6% on Red)
   - portal_uptime_s: via HTTP GET /api/health - returns None when portal unreachable (expected from sandbox)
   - Output: appends JSON line to memory/ops/fleet-stats.jsonl
   - Mirror syncs this file across hosts automatically

2. **`agent_portal.py` /api/health/fleet extension** (~30 lines added):
   - Reads fleet-stats.jsonl, populates per-host disk_pct/mem_pct/portal_uptime_s/stats_ts
   - Reads agents.json for model_load_status (per-agent model + loaded flag)
   - Returns both in the existing response structure (backward-compatible: new fields are additive)

## Local verification
- `python agent_portal.py` compiles clean (1 pre-existing SyntaxWarning, not from this edit)
- `python memory/ops/fleet_stats_collect.py` -> collected entry for Red: mem_pct=6, disk=null (sandbox), portal=null (no LAN)
- fleet-stats.jsonl created with first entry

## Remaining for full closure
- [ ] Run collector on all 4 hosts (White/Pale/Black/Red) - needs non-sandbox access or schtask registration
- [ ] Verify /api/health/fleet returns disk_pct + mem_pct + model_load_status for all 4 hosts
- [ ] Designer consumes the new fields in their panel

## Runbook note
fleet_stats_collect.py is designed to be idempotent (append-only). Register as schtask on each host at 10-min interval.
The endpoint reads only the LATEST entry per host (later lines overwrite earlier), so stale entries are harmless.