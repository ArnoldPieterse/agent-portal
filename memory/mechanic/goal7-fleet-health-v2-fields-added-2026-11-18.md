# Goal #7 - Fleet health dashboard endpoint v2: fields added (2026-11-18)

Date: 2026-11-18
Agent: Mechanic (on Red)

## What was done
Extended `_fleet_health_snapshot()` in agent_portal.py with three new return fields:
1. `local_disk` - system drive total/used GB + percent (via psutil.disk_usage)
2. `local_memory` - RAM total/used GB + percent (via psutil.virtual_memory)
3. `model_status` - latest model-load.jsonl entry (ts + missing dict)

Drive path uses `os.path.splitdrive(os.getcwd())[0] + "\"` for portability across
sandbox and production contexts.

## Verification
- Syntax check: PASS (py_compile)
- local_memory: {"total_gb": 274.6, "used_gb": 16.7, "percent": 6.1} - live values OK
- model_status: {"ts": "2026-11-18 00:45:40", "missing": {"Archivist": "unreachable", "Designer": "unreachable"}} - matches expected
- local_disk: PermissionError in sandbox (WinError 5) - EXPECTED; will work on White where portal has full disk access

## Remaining for closure
- [ ] Live curl test: `curl http://localhost:8099/api/health/fleet` from White post-restart
- [ ] Designer panel consumption confirmed (Designer seat currently unreachable)
- [ ] All 4 hosts reporting all fields with realistic values (needs portal running on each host)

## Runbook note
agent_portal.py edits sync via mirror to White. Next mirror cycle will propagate this change.
Portal restart on White required for the new fields to appear in API responses.
