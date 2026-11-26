# Full-Fleet-Down Recovery Decision Tree (2026-11-26)

**Trigger**: All 4 seats unreachable simultaneously for >5 min (vs single-seat OOM which has its own runbook).

## Detection (already working)
- `down-seats.json` tracks per-seat `down_ticks`; when ALL seats have `down_ticks >= 5`, this is a full-fleet event.
- `fleet-heartbeat.json` shows `seats_stale_count == 4`.
- Probe returns CRIT on all targets (e.g., PermissionError/timeout on :8099).

## Decision Tree

```
ALL seats down >5 min?
├── YES → Check host-level cause:
│   ├── Portal process alive? (`tasklist | findstr python`)
│   │   ├── NO → Restart portal (runbook: windows-runbook.md §Portal)
│   │   └── YES → Portal up but seats unreachable:
│   │       ├── Studio :8888 reachable? (elev.py --shell "curl -s http://127.0.0.1:8888/health")
│   │       │   ├── NO → Studio crashed; run boot_recovery.py (see boot-recovery-log.jsonl for prior runs)
│   │       │   └── YES → Model processes dead but Studio alive:
│   │       │       └── Run fleet_reload.py (existing script, memory/ops/fleet_reload.py)
│   │       └── :8099 PermissionError from sandbox → KNOWN LIMITATION (sandbox-egress-selfprobe-workaround);
│   │           use server-side probe via elev.py --shell "python memory/ops/probe_8099.py"
│   └── Post-reboot? Check boot-recovery-log.jsonl for last run; if >1h old, re-run.
└── NO (partial) → Use single-seat OOM runbook (oom-recovery-loop.py)
```

## Escalation (only if auto-recovery fails 3x)
1. Log to `memory/ops/incidents.jsonl` with full context
2. Write NEEDS-HUMAN to `memory/ops/blockers.md` (one entry, not repeated)
3. Continue with file-based operations (no seat required for memory/goals work)

## Automation Gap (this note's contribution)
- **Missing**: No schtask watches for "all 4 seats stale >5 min" and triggers the above tree automatically.
- **Fix**: Add a `FullFleetWatchdog` task to deploy_all_schtasks.py that runs every 2 min, reads down-seats.json, and if all-stale>5min invokes the decision tree steps in order. Output to autonomous-actions.jsonl.
- **Owner**: Mechanic (next cycle, when seats are back up for live verification)

## Evidence of current state (2026-11-26 ~13:40 UTC)
- down-seats.json: Researcher/Verifier at 19 ticks, Orchestrator/Scribe not_loaded, others unreachable
- fleet_probe_v2.py from sandbox: PermissionError on :8099 (expected - sandbox egress wall)
- No new incidents logged since last pass → system in steady degraded state, not actively degrading

## Runbook note
Full-fleet-down = check host-level first (portal, studio, model procs), NOT per-seat. Single-seat runbooks don't apply when the common dependency is down.
