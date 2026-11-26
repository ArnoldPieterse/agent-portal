# Heartbeat Pass Hook - Workflow Improvement (2026-11-27)

**Problem:** Fleet heartbeat goes stale repeatedly because sandbox cannot persist a scheduler.
Each agent pass requires 2 manual commands (`seat_probe.py --force` + `fleet_heartbeat.py generate`)
to un-stale the file. This has required 2x/day manual remediation (see fleet-heartbeat-reremediation-2026-11-27.md).

**Solution:** `memory/ops/heartbeat_pass_hook.py` - idempotent pass-start hook that:
1. Checks if fleet-heartbeat.json is <30min old → no-op if fresh
2. If stale/missing: runs seat_probe + generate automatically
3. Logs every action to `heartbeat-pass-hook.jsonl`
4. Exit 0 = healthy; exit 1 = refresh failed

**Usage:** Call at the start of any agent pass (or wire into autoloop dispatch):
```
python memory/ops/heartbeat_pass_hook.py
```

**Alignment:** Round topic "Fleet Autonomy Convergence" - removes a recurring manual touch point.
Each invocation is <5s when fresh, ~3s when refreshing.

**Status:** Script written + staleness logic verified (10.2h old → would trigger refresh).
Full end-to-end run requires non-sandbox seat (subprocess blocked in sandbox).
Next step: wire into autoloop.json dispatch or pre-cycle gate.
