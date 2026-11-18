# Goal #7 Progress: Fleet Health Dashboard Endpoint v2
Date: 2026-11-18
Agent: Mechanic (on Red, sandbox)
Status: CODE PATCHED - disk/memory/model fields added to /api/health/fleet

## What was done
Extended `_fleet_health_snapshot()` in agent_portal.py with three new response fields:
1. `local_system.disk` - total/used/free MB + pct_used via shutil.disk_usage()
2. `local_system.memory` - total/used MB + pct_used via psutil.virtual_memory()
3. `model_status[]` - per-agent name, model_id, loaded flag from agents.json

Remote hosts still return None for system stats (no WinRM; consistent with existing design).
Portal uptime (`portal_uptime_s`) was already present from cycle-2 goal 8.

## Verification
- Syntax check: py_compile PASS (one pre-existing SyntaxWarning in comment, not from this change)
- psutil confirmed available in sandbox environment
- agents.json has all 8 agents with model_id fields

## Remaining for full closure
- [ ] Live endpoint test on White (portal restart + curl /api/health/fleet to confirm new fields appear)
- [ ] Verify remote hosts show disk/memory as null (not error)
- [ ] Designer panel integration (consume the new fields)

## Runbook note
Edit is additive - existing response fields unchanged. Safe to deploy: worst case, new fields are null if psutil/shutil unavailable. No breaking changes.
