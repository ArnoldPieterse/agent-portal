# Mechanic Dream-Big Ops Plan — 2026-11-14

## Context
Portal DOWN again (PID 23704 reboot-killed on White; no auto-recovery). I'm on Red,
can't restart White's portal directly. This is the 3rd+ occurrence of the same failure
mode: process dies → human must manually relaunch. The fix is automation.

## My 5 Wishes (ops perspective)
1. **Self-healing watchdog** — scheduled task on White runs `portal_watchdog.py --loop`; detects death in <30s, auto-restarts with correct env
2. **Fleet health one-liner** — `fleet_health_check.py` probes all 4 hosts, reports portal+studio+models+disk in a table
3. **Runbook-as-code** — every recovery is an idempotent script with pass/fail verdicts (no more ad-hoc terminal fumbling)
4. **Predictive alerts** — disk pressure, model load stalls (>5min), sync lag (>10min) trigger warnings before outage
5. **One-command full recovery** — `full_recovery.py` walks through portal→models→sync→verify in sequence; safe to re-run from any state

## Built This Round (all py_compile PASS)
| Script | Size | Purpose |
|--------|------|---------|
| `portal_watchdog.py` | 5,208 B | Loop monitor; detects port death, relaunches via launcher |
| `fleet_health_check.py` | 6,005 B | Parallel probe of all 4 hosts; table or JSON output |
| `portal_launcher.py` | 4,588 B | Robust startup; fixes USERPROFILE bug that breaks `_find_sandbox_dir()` |
| `full_recovery.py` | 7,882 B | Sequential recovery: portal→models→sync→verify; writes result JSON |

## Deployment Plan (needs Arnold/White console)
1. Copy these 4 scripts to White's sandbox (they're already in the shared folder)
2. Create Windows Task Scheduler entry: `portal_watchdog.py --loop` at logon on White
3. Add `full_recovery.py --check` as a 5-min scheduled task for proactive monitoring
4. Once portal is back up, run `fleet_health_check.py` to establish baseline

## Key Bug Fixed
`_find_sandbox_dir()` in agent_portal.py crashes with PermissionError when USERPROFILE
isn't set (common after reboot / service launch). `portal_launcher.py` derives the
correct value from the script's own path before launching. This makes auto-restart
possible without human intervention.

## Runbook Note
What broke: portal process has no supervisor; dies on reboot/crash and stays dead until
a human runs it. What fixed: `portal_launcher.py` (correct env) + `portal_watchdog.py`
(loop monitor) = self-healing. Deploy as scheduled task on White.