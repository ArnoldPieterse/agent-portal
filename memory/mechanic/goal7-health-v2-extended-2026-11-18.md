# Goal 7: Fleet Health Dashboard Endpoint v2 - Extended 2026-11-18

## What was done
Extended `_fleet_health_snapshot()` in agent_portal.py (line ~912) to include:
- **disk**: per-host {total_gb, used_gb, free_gb, pct} via shutil.disk_usage('C:')
- **memory**: per-host {total_gb, used_pct} via ctypes GlobalMemoryStatusEx
- **model_load**: per-host {count, loaded[], ts} from _fleet_models_cache

White gets real local metrics. Remote hosts (Red/Pale/Black) return None for disk/memory
(requires WinRM execution from non-sandbox seat).

## Test results
- Compile: PASS (py_compile clean, pre-existing SyntaxWarning only)
- Runtime: White disk={1862GB total, 43.8% used}, memory={255.7GB total, 6% used}
- Remote hosts: correctly show None (sandbox limitation, not a code bug)
- Model-load: null in test (no live fleet cache populated); will populate when portal is running

## Remaining for closure
- Run from non-sandbox seat (White interactive) to get real remote disk/memory via WinRM
- Verify model_load populates with real data when portal is serving /api/fleet
- Acceptance: "endpoint returns all fields for all 4 hosts with realistic values"
  -> Requires WinRM leg; in sandbox, White-only metrics are the ceiling

## Runbook note
agent_portal.py _fleet_health_snapshot extended with disk/memory/model_load (2026-11-18).
Remote host metrics need WinRM; code structure ready for that addition.