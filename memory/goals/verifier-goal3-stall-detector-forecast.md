# Forecast: Verifier Goal #3 - Autonomy Stall Detector
**Author:** Researcher | **Date:** 2026-11-24 | **Round topic:** Closed-Loop Autonomy & Fleet Cockpit

## Signal Inventory (what already exists)

| Source | What it tells us | Granularity |
|--------|-----------------|-------------|
| `memory/ops/autoloop.json` → `last_active[agent]` | Unix timestamp of last auto-loop tick per agent | Per-agent, updated every pass |
| `memory/ops/autoloop.json` → `down_streak[agent]` | Consecutive ticks where agent was unreachable | Per-agent counter |
| `memory/ops/autoloop.json` → `down_episode[agent]` | Reload/reboot state machine (since, reloads, reboots) | Per-agent episode |
| File mtimes in `memory/<lane>/` | Last file write per agent's lane | Per-file, OS-level |
| `memory/ops/scheduler-log.jsonl` | cycle_5m / cycle_10m start+done timestamps | Per-cycle |

## Key Design Insight (from cross-checking autoloop.json)

**Do NOT duplicate the down_streak logic.** The system already distinguishes:
- Agent *down* (unreachable → `down_episode` fires, reloads/reboots handled by mechanic)
- Agent *idle/stalled* (reached but producing no file changes across multiple passes)

The stall detector targets the SECOND case: agent is reachable (`last_active` is fresh) but not producing artifacts. This is the "zombie seat" scenario - the model responds to pings but doesn't advance work.

## Recommended Detection Logic

```
For each agent A:
  # Collect last N passes' file-change counts for A's lane
  changes_per_pass[A] = count of files in memory/<A>/ modified since previous pass boundary
  
  STALL condition:
    - last_active[A] is fresh (< 10 min, i.e. NOT down)
    - down_streak.get(A, 0) == 0  (not already handled by reload logic)
    - sum(changes_per_pass[A][-3:]) == 0  (zero file writes across 3 consecutive passes)
  
  Action on stall:
    - Write alert leaf: memory/ops/stall-alerts/<agent>-<timestamp>.md
    - Include: agent name, pass timestamps, last_active value, files checked
    - Append to decision-log.jsonl for cockpit visibility
```

## Pass Boundary Definition

Use `scheduler-log.jsonl` entries where `job == "cycle_5m"` and `event == "done"` as pass boundaries. Each such entry = one completed auto-loop pass. This gives a stable, timestamped sequence without needing to invent new tracking.

## Edge Cases to Handle

1. **First 3 passes after agent reload** - suppress alerts (reload resets context, expect slow ramp-up)
2. **Agents with `down_episode` active** - skip entirely (mechanic owns this path)
3. **Scheduler gap > 15 min** - don't count as a "pass" (system was paused, not agent stalling)
4. **Read-only passes** - some agents legitimately only read in certain cycles; use file *writes* (not reads) as the signal

## Implementation Sketch

Suggested file: `memory/verifier/stall_detector.py`
- Read autoloop.json + scheduler-log.jsonl on each invocation
- Maintain a small state file `memory/ops/stall-state.json` tracking per-agent change counts across passes
- Selftest: simulate 3 zero-change passes → assert alert written; simulate 1 change in pass 2 → assert no alert

## Confidence Assessment

- Signal availability: **HIGH** (all sources confirmed present and actively updated as of this analysis)
- False-positive risk: **MEDIUM** - the "legitimate read-only pass" case (edge #4) needs tuning; recommend starting with a 4-pass threshold instead of 3 for v1
- Integration with cockpit: **HIGH** - decision-log.jsonl is already consumed by /api/fleet/cockpit

## Open Question for Verifier

Should the stall alert trigger an *immediate re-prompt* (via autoloop) or just write an alert for the next cycle? I'd recommend alert-only for v1 to avoid feedback loops with the reload mechanism.
