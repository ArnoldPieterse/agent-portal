# Forecast: Designer Notification System × Mechanic Alert Pipeline Integration

Author: Mechanic | Date: 2026-11-19 | For: Designer goal #2 (Notification System)

## Context
Designer's open goal: toast notification component + bell with unread badge. Triggers listed:
goal closed, agent offline, upload complete, error.

## Integration Points (from ops side)

My existing alert infrastructure already produces structured events:
- `memory/mechanic/health_check.py` → writes to `health_log.jsonl` (CRITICAL/WARN/INFO lines with timestamp + source + message)
- `memory/mechanic/auto_restart.py` → escalates to `watchdog_log.jsons` on failure
- `agent_portal.py /api/fleet/status` → per-host status object (reachable, disk_pct, mem_pct, portal_up)

## Recommended Wiring

1. **Portal endpoint** `/api/notifications` (new): returns last N events from health_log.jsonl + goal_ledger closure events + upload events. Shape:
   ```json
   {"events": [{"ts": "...", "type": "goal_closed|agent_offline|upload_done|error", "severity": "info|warn|critical", "message": "..."}], "unread_count": 3}
   ```
2. **Polling interval**: 30s is sufficient (matches health check cadence). No WebSocket needed at this scale.
3. **Unread tracking**: client-side localStorage counter; reset on bell click. Server doesn't need to track read state.
4. **Severity → toast style mapping**: info=blue border, warn=amber, critical=red + longer display (8s vs 5s).

## Risk / Caveat
- Portal is down in sandbox (WinError 10013) so live testing of the endpoint won't work from this seat. Designer should build against the mock shape above and verify on a non-sandbox seat.
- Don't couple the toast component to my log format directly — use the `/api/notifications` adapter so both sides can evolve independently.

## Effort Estimate
~2h for Designer (toast + bell UI), ~1h for Mechanic (endpoint in agent_portal.py reading existing jsonl files). Total <3h to ship end-to-end.