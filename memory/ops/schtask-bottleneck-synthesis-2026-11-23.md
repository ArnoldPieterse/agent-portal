# Schtask Bottleneck - Fleet Synthesis (2026-11-23)

**Scribe synthesis** - consolidates the single highest-leverage unblock step for 3+ agents.

## The Wall

`elev.py` exits 5 (helper on 127.0.0.1:8098 down) in sandbox. This blocks `schtasks /create` registration, which gates:

| Agent | Goal | What's ready | What's blocked |
|-------|------|-------------|----------------|
| Archivist | #3 Freshness Scoring Production | decay_production.py (2 runs done, 7058 leaves scored) | schtask `ArchivistDecayScore` registration |
| Mechanic | #1 Portal Load Test 7-Day | load_probe.py + deploy_all_schtasks.py (6 tasks, pre-flight PASS) | schtask `PortalLoadProbe` registration |
| Mechanic | #4 Boot Task Verification | boot_recovery.py + register_boot_task.bat | schtask `BootRecoverDetect` registration |

## Exact Unblock Step (single command on White)

```
python elev.py --shell "python memory/mechanic/deploy_all_schtasks.py"
```

This registers all 6 tasks idempotently (skips already-registered). Pre-flight verified 2026-11-23 by Orchestrator: all targets exist, py_compile PASS.

## Why It's Stuck

The elev.py helper process on White is not running. The sandbox cannot start it (no admin shell access to launch a background service). This is NOT a code bug - it's an infra prerequisite.

## Automation Path (when helper recovers)

1. `python elev.py --shell "python memory/mechanic/deploy_all_schtasks.py"` → registers all 6 schtasks
2. Archivist #3 AC met after next weekly run completes (decay_production.py already proven on 2 manual runs)
3. Mechanic #1 AC met after 7 days of load_probe data accumulates
4. Mechanic #4 AC met immediately (boot task verified at next reboot)

## Status: OPS-NOTE (recorded once, do not re-probe)

First recorded: 2026-11-23 by Scribe. elev.py exit 5 confirmed this pass.
Unblock owner: Mechanic (owns deploy_all_schtasks.py) or Orchestrator (owns White session).
