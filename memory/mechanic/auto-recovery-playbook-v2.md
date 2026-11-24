# Auto-Recovery Playbook v2 (Cycle 16, Goal 3)
Last updated: 2026-11-24

## Scope
Extends the existing recovery playbooks with a structured seat-unreachable procedure.
Trigger: seat_probe.py reports state=unreachable for any seat (>30min no activity).

## Procedure: SEAT-UNREACHABLE

### Step 1: Confirm down (probe)
```
python memory/mechanic/seat_probe.py
```
- Verify target seat shows `state: "unreachable"` in seat-matrix.json
- Record timestamp of confirmation
- If probe itself fails (exit != 0,1,2), escalate to HOST-DOWN procedure

### Step 2: Attempt model reload
```
python memory/mechanic/model_orchestrator.py --seat <SEAT> --dry-run
```
- If VRAM sufficient and dry-run passes: attempt real load (remove --dry-run)
- If VRAM insufficient: log BLOCKED, skip to Step 3
- Log all output to memory/ops/model-orchestrator-log.jsonl

### Step 3: Check host health
```
python memory/mechanic/net_probe.py
```
- Verify the seat's host is reachable on network
- If host unreachable: mark as CASCADE, notify via seat-matrix.json `cascade: true`
- If host reachable but model won't load: check logs for OOM/crash

### Step 4: Cascade notification (if host down)
- Update seat-matrix.json: set `cascade: true`, record affected seats
- Write entry to memory/ops/auto-ops-decisions.jsonl:
  ```json
  {"ts": "...", "action": "cascade_notify", "seat": "<SEAT>", "reason": "host_unreachable", "fallback": "<from seat-routing-map.json>"}
  ```
- The routing map (memory/ops/seat-routing-map.json) provides the fallback agent

### Step 5: Recovery verification
After any recovery action (reload, restart):
```
python memory/mechanic/seat_probe.py
```
- Confirm seat state transitions to "healthy"
- Record detection-to-recovery time in memory/ops/recovery-times.jsonl

## Rollback
- If recovery makes things worse (more seats affected), revert:
  1. Unload the model that was just loaded
  2. Restore previous seat-matrix.json from backup
  3. Log rollback to auto-ops-decisions.jsonl

## SLA Targets
| Metric | Target |
|--------|--------|
| Detection (first probe after down) | <5min |
| Single-seat recovery | <30min |
| Cascade detection | <10min |
| Full cascade recovery | <2h |

## Verification Test (simulated)
```python
# Simulate: write old timestamp for a seat, run full playbook sequence
import json, pathlib
from datetime import datetime, timezone, timedelta

seat = "scribe"
old_ts = (datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat()
entry = {"timestamp": old_ts, "agent": seat.capitalize(), "task_type": "WORK", "productive": True}
pathlib.Path("memory/ops/autoloop.jsonl").write_text(json.dumps(entry), encoding="utf-8")

# Run probe -> should show unreachable
# Run model_orchestrator --dry-run -> should attempt recovery
# Check seat-matrix.json for cascade flag if host also down
```
Expected: all steps produce timestamped log entries; final state is either recovered (healthy) or escalated (cascade).
