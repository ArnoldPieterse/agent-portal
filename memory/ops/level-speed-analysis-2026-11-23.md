# Level-Speed Analysis — why a level took >1h (2026-11-23)

Question: "we have been stuck on lvl 0 for more than an hour. one level should not take more than an hour on average."

## What actually happened (cycle-8, the cycle that earned Lv 1)

Timeline reconstructed from git log (2592 commits) + watchdog.log:

| Window | Duration | State |
|---|---|---|
| Nov 20 ~goal-set -> Nov 21 02:45 | ~39h | active (commits every few min), machine then went dark |
| **Nov 21 02:45 -> Nov 22 13:47** | **35.0h** | **TOTAL SILENCE — no commits, no watchdog fires at all** |
| Nov 22 13:47 -> Nov 23 02:28 | ~12.7h | active: remaining goals completed (fleet re-home, load queues, placement) |

- Cycle-8 wall time ≈ 2.9 days; **the 35h silence is 60% of it.**
- Level counter itself was also blind to completion until the 120s heartbeat fix (commit 9d16305d, Nov 23 06:34) — cycle-8 sat un-leveled 02:28->06:00. Both bugs compounded.

## Root cause of the 35h silence

White (this host) was **asleep/off** from ~Nov 21 02:45 to ~Nov 22 13:42:
- PortalWatchdog fires every 5 min via schtask and logged NOTHING in that window (last fire Nov 20 09:27, next Nov 22 13:42 "DOWN detected -> running PortalRun"). A dead portal with a healthy machine would have left watchdog entries; zero entries = the task scheduler itself wasn't running = machine asleep.
- First commit after wake (13:47) is 5 min after the first watchdog fire — exactly the restart latency.
- System event log rotated (only covers today), so no sleep events to quote; absence of ALL local activity for 35h is the evidence.

## Secondary factors (active time still ~13h, not 1h)

- 4/8 seats unreachable mid-cycle (Researcher/Archivist/Scribe/Mechanic) -> their goals waited for recovery.
- Model-load contention on Black: repeated `load -> 409 active_generations` in the recovery chain; models unload under VRAM pressure (anomaly report flags 6-8/8 agents unloaded windows).
- Goal rounds are big (8-goal Orchestrator rounds across 8 agents, local 27B models) — a healthy full round is multi-hour by construction.

## Fixes applied (2026-11-23)

1. **Power plan: sleep/hibernate on AC = never** (`powercfg /change standby-timeout-ac 0`, `hibernate-timeout-ac 0`; verified index 0x0). Kills the 35h-gap class while plugged in.
2. **PortalGapAlarm schtask (every 5 min) + gap_alarm.py**: if HEAD unchanged >60min while a goal cycle is open+incomplete -> writes `memory/ops/gap_alarm.json` flag + appends `memory/ops/gap-alarm.log`; clears on resumed activity. Stalls now surface in ~65 min instead of silently.
3. (Earlier today) 120s level-check heartbeat in agent_portal.py — completion detected within minutes, not on next page load.

## To actually get toward ~1h/level (needs decision)

- Smaller rounds: e.g. 4-goal batches or per-agent micro-goals so "all goals reached" happens more often with less work per gate.
- Faster inference: smaller/faster models on the fleet, or fewer concurrent heavy loads (the 409 wall is load contention).
- Keep seats reachable: auto-recovery of unreachable seats is already chained; the remaining lever is host uptime (same power fix for Red/Black/pale if they sleep).

## Files

- `gap_alarm.py` (new, root) + schtask `PortalGapAlarm`
- `memory/ops/gap-alarm.log` (alarm history)
- evidence: git log gaps analysis, `memory/ops/watchdog.log`, `memory/ops/anomalies-2026-11-22.md`
