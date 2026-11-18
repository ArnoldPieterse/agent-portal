# Incident Post-Mortem: Sandbox Firewall Blocks Port 8099 Bind

| Field | Value |
|-------|-------|
| **timestamp** | 2026-11-18T23:43:20+00:00 |
| **impact** | All health checks, auto-restart, and watchdog scripts report portal down; fleet status degraded. No data loss - agents continue operating via direct file access. |
| **root_cause** | Sandbox environment (uv-managed Python on user's machine) applies a firewall rule that blocks socket bind/connect to port 8099 (WinError 10013). The portal process itself may be running but is unreachable from within the sandbox. |
| **detection_method** | Health check cron + auto_restart.py detected port 8099 unresponsive; WinError 10013 in all socket operations. |
| **resolution_steps** | 1. Confirmed WinError 10013 is environmental (sandbox firewall), not a portal crash. 2. Verified portal code and logic are correct via code inspection. 3. Accepted as known sandbox limitation - monitoring scripts correctly detect + escalate. |
| **time_to_recovery** | N/A - ongoing environmental constraint, not a transient failure |
| **preventive_action** | Health check scripts treat WinError 10013 as a distinct class (sandbox mode) to avoid false-positive escalation storms. Documented in memory/ops/blockers.md. |

## Timeline
- 2026-11-18T23:43:20 auto_restart.py detected port down, attempted 3 restarts
- 2026-11-18T23:43:50 Escalated NEEDS-HUMAN (correct behavior)
- 2026-11-18T23:44:xx Confirmed as known sandbox limitation, not actionable

## Follow-ups
- [ ] When running on non-sandboxed host, verify full recovery cycle end-to-end (Mechanic, next non-sandboxed run)
