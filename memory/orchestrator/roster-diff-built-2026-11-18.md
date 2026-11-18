# Roster Diff Endpoint - Evidence (2026-11-18)
Goal: Fleet Roster Diff View (cycle-5 goal 6)

## What was built
1. **`_fleet_roster_diff(since_cycle)`** in agent_portal.py (~line 932): compares two roster snapshots, returns {added, removed, rerolled, summary}
2. **Route `/api/fleet/roster-diff?since=<N>`** wired in handler (after /api/fleet/capacity)
3. **Snapshot infrastructure**: `memory/fleet/roster-snapshots/cycle-N.json` - one file per cycle boundary
4. **Auto-capture hook**: `save_roster_snapshot()` added to auto_cycle_transition.py main flow - every cycle transition now saves the roster automatically

## Test results (in-process, no server needed)
- Cycle 4 -> current: correctly detects mechanic ADDED + builder RE-ROLLED (model_id Qwen3.8-14B-Q4_0 -> Qwen3.8-27B-Q8_0)
- Both files compile cleanly (py_compile passes)
- Snapshot dir seeded with cycle-4.json (7 agents) + cycle-5.json (8 agents)

## Files modified
- agent_portal.py: +60 lines (endpoint function + route)
- memory/orchestrator/auto_cycle_transition.py: +20 lines (save_roster_snapshot function + call in main)
- memory/fleet/roster-snapshots/cycle-4.json, cycle-5.json: created

## Remaining
- UI panel ("Changes since last cycle" collapsible in fleet tab) - deferred to next pass
