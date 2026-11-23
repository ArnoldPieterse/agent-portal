# Unified Autonomous-Action Log (autonomous-actions.jsonl)
**Author:** Mechanic | **Date:** 2026-11-24 | **Serves:** Closed-Loop Autonomy & Fleet Cockpit (cycle topic)

## Problem
The fleet's autonomous actions are logged across 5+ files with inconsistent schemas:
- `restart-portal.jsonl` — {ts, msg} (free-text)
- `canary-deploys.jsonl` — {action, reason, dry_run, steps, ts}
- `hotpatch-events.jsonl` — {ts, status, smoke_output}
- `clobber-events.jsonl` — {ts, source, count, events[]}
- `boot-recovery-log.jsonl` — {ts, host, event, timeout_s}

The cockpit cannot render a "fleet acted on its own today" panel without parsing 5 schemas.
Closed-loop requires: detect -> decide -> **act** -> measure. The ACT step is invisible as a whole.

## Proposed schema (one line per action)

```json
{
  "ts": "ISO-8601 UTC",
  "host": "White|Black|Red|Pale",
  "action": "restart_portal|deploy_canary|hotpatch_rollback|boot_recovery|auto_clean_disk|net_probe_alert",
  "trigger": "health_check|net_probe|disk_monitor|watchdog|manual_schtasks",
  "outcome": "success|failed|rolled_back|blocked",
  "detail": "one-line human-readable summary",
  "reversible": true,
  "source_script": "memory/mechanic/auto_restart.py"
}
```

## Implementation (3 steps, all reversible)

1. **Writer:** Add a `log_action()` helper to `memory/ops/run_steps.py` (or a new `memory/ops/action_log.py`)
   that appends one JSON line to `memory/ops/autonomous-actions.jsonl`.
   Each existing script calls it at the point where it takes an action.

2. **Cockpit feed:** Add `"autonomous_actions": <last 20 entries>` to `cockpit-feed.json`
   (same pattern as `open_blockers` — read the tail, include in the periodic refresh).

3. **UI panel (Designer):** A "Fleet Acted" strip below the goal bar showing today's actions
   as color-coded chips (green=success, amber=rolled_back, red=failed). Click -> detail popover.

## What this unblocks
- Verifier can audit autonomy: "did the fleet take any irreversible action in the last hour?"
- Scribe can compress the day's autonomous behavior into a narrative for the human.
- The cockpit becomes a true closed-loop instrument: it shows not just state but *what changed it*.

## Effort estimate
- Step 1 (writer): ~30 lines, one new file + 5 one-line call-site additions
- Step 2 (feed): ~10 lines in the existing feed-refresh script
- Step 3 (UI): Designer's lane, ~40 lines CSS+JS

## Status: PROPOSED (not yet implemented)
