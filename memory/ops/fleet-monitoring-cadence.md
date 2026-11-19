# Fleet Monitoring Cadence & Escalation Policy
Updated: 2026-11-19 (Mechanic)

## What runs when

| Interval | Script | Checks | Evidence |
|----------|--------|--------|----------|
| 5 min | memory/mechanic/health_check.py | portal HTTP 200, disk <80%, mem <90% | portal notification + stdout |
| 10 min | memory/mechanic/net_probe.py | TCP to all 4 hosts, latency, consecutive-fail count | net_probe.state.json |
| 30 min | memory/mechanic/disk_monitor.py | disk pct per host; auto-clean if >85% | stdout + --clean log |
| on-kill | memory/mechanic/auto_restart.py | portal process alive? restart max 3x, 10s wait | restart-portal.jsonl |
| on-fork | memory/mechanic/portal_watchdog.py | PID valid, port bound, no zombie children | watchdog.log |

## Escalation path (3 tiers)

TIER 1 - Auto-recover (no human)
  health_check detects portal down
    -> ../mechanic/auto_restart.py fires (3 attempts x 10s)
    -> if recovered: log entry, continue
    -> if still down after 3: escalate to TIER 2

TIER 2 - Alert + diagnose (agent attention)
  net_probe: >3 consecutive failures OR p95 >200ms
  health_check: disk >85% or mem >90%
    -> portal notification (CRITICAL/AMBER)
    -> check memory/ops/blockers.md for known wall
    -> if known wall: log once, move on
    -> if new: write post-mortem skeleton via postmortem_gen.py

TIER 3 - NEEDS-HUMAN (exact unblock step in blockers.md)
  auto-restart exhausted (3x fail)
  disk >90% after auto-clean
  host unreachable >30 min
    -> memory/ops/blockers.md entry: {timestamp, host, command, error, exact unblock}
    -> no re-probe of same wall in subsequent passes

## Known walls (do NOT re-probe)

- Sandbox egress block (WinError 10013): portal HTTP probes from sandbox seat fail. Documented since 2026-11-17. Workaround: use elev.py or check from non-sandbox host.
- Scheduled tasks not visible in sandbox: use `python elev.py schtasks /query` for task state.

## Recovery time expectations (from recovery-matrix.md)

| Host | Expected auto-recovery | Manual fallback |
|------|----------------------|------------------|
| White  | <30s (auto_restart)  | elev.py --shell "python agent_portal.py &" |
| Black  | <60s (boot task)     | RDP + manual start |
| Red    | <60s (boot task)     | RDP + manual start |
| Blue   | N/A (not deployed)   | deploy_boot_recovery_fleet.py |

## Runbook note format (one-liner in runbook-notes.md)

[YYYY-MM-DD HH:MM] <what broke> -> <what fixed it> (host, script)
