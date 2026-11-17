# Goal #7 - Fleet health dashboard endpoint v2 (progress)

Date: 2026-11-18
Agent: Mechanic
Seat: Red sandbox (cannot reach :8099 for live verification)

## What was done
Extended `_fleet_health_snapshot()` in agent_portal.py with three new top-level fields:

1. **`disk`** - per-host disk usage dict. White gets real values via `shutil.disk_usage()`;
   remote hosts (Red/Pale/Black) get `null` (probe doesn't collect disk yet).
2. **`memory`** - per-host memory usage dict. White gets real values via `psutil.virtual_memory()`;
   remote hosts get `null`.
3. **`model_load`** - latest entry from `memory/ops/model-load.jsonl` (shows which agents are
   missing/unreachable on the most recent auto-loop run).

## Schema (new response shape)
```json
{
  "ok": true,
  "generated": "2026-11-18 ...",
  "hosts": { ... existing per-host probe+sync data ... },
  "last_probe_line": "...",
  "git_head": "...",
  "git_goals_last_change": "...",
  "portal_uptime_s": 12345,
  "disk": {
    "White": {"total_mb": 1906610, "used_mb": 836117, "free_mb": 1070493, "pct": 43.9},
    "Red": null, "Pale": null, "Black": null
  },
  "memory": {
    "White": {"total_mb": 261855, "used_mb": 15533, "pct": 5.9},
    "Red": null, "Pale": null, "Black": null
  },
  "model_load": {"ts": "...", "run": "...", "missing": {...}}
}
```

## Verification status
- [x] Code written + compiles clean (py_compile PASS)
- [x] Local disk/memory values confirmed realistic (43.9% disk, 5.9% mem on White)
- [ ] Live endpoint test: requires non-sandbox seat to hit http://127.0.0.1:8099/api/health/fleet
- [ ] Remote host disk/memory: needs probe enhancement (future - not in scope for this pass)

## Remaining for full closure
1. Restart portal on White (or wait for watchdog) to pick up the code change
2. Hit /api/health/fleet from a non-sandbox seat, confirm all fields present
3. Record via `python memory/researcher/goal_ledger.py --record mechanic 7`

## Runbook note
Goal #7 v2 adds disk/memory/model_load to /api/health/fleet. Remote host metrics are null until
the fleet probe is enhanced to collect them (separate task). Local (White) values are live.
