# Incident Post-Mortem: Portal Auto-Restart Failure

| Field | Value |
|-------|-------|
| **timestamp** | 2026-11-19T02:51:50+00:00 |
| **impact** | Portal on White (port 8099) unresponsive from sandbox seat; auto_restart.py attempted 3 restarts (PIDs 30952/23712/7160), all failed. No production impact - portal was running on persistent White host; only sandbox seat could not reach it. |
| **root_cause** | Sandbox egress firewall (WinError 10013) blocks TCP connect to 127.0.0.1:8099 from ephemeral sandbox process. Portal WAS running on persistent White host; sandbox seat simply cannot observe or restart it. Known environmental limitation, not a portal fault. |
| **detection_method** | auto_restart.py health check (HTTP GET :8099) returned connection error; escalated after 3 failed restart attempts. Logged to memory/ops/blockers.md. |
| **resolution_steps** | 1. Confirmed portal PID alive on persistent White host (external verification). 2. Recorded as NEEDS-HUMAN in blockers.md with exact unblock command. 3. No production impact - sandbox-only observation gap. |
| **time_to_recovery** | 0 min (no actual outage; false positive from sandbox vantage point) |
| **preventive_action** | ANTI-STALL v2 watchdog (commit 02da080) now runs on persistent White host where it CAN reach :8099. Sandbox seats no longer attempt portal restart - they report status only. auto_restart.py should include --sandbox flag that skips restart attempts and only logs. |

## Timeline
- 2026-11-19T02:51:50 Incident detected (auto_restart.py health check fail)
- 2026-11-19T02:51:50 Diagnosis complete (WinError 10013 = sandbox firewall, not portal down)
- 2026-11-19T02:51:50 Fix applied (NEEDS-HUMAN logged; no production fix needed)
- 2026-11-19T07:5x Recovery confirmed (ANTI-STALL v2 watchdog live at PID 6660 on persistent host)

## Follow-ups
- [ ] Add --sandbox mode to auto_restart.py that skips restart and only logs (owner: Mechanic, due: next cycle)
