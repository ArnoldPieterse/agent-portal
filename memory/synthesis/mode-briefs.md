# Mode Decision Briefs

## Transition 1: WORK -> MAINTENANCE (2026-11-24T08:00:00)

At 2026-11-24T08:00:00Z, the fleet transitioned from WORK to MAINTENANCE. Before the change, 95.0% of tracked goals were complete. This was triggered because: cycle_closeout. Agents will switch to role-specific maintenance tasks from the idle-rotation table; new goal work is paused.

## Transition 2: MAINTENANCE -> WORK (2026-11-24T12:00:00)

At 2026-11-24T12:00:00Z, the fleet transitioned from MAINTENANCE to WORK. Before the change, 0.0% of tracked goals were complete. This was triggered because: a new work cycle was initiated with fresh goals. All agents will resume working their open goals from the next10.json queue.
