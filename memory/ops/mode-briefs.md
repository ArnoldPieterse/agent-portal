# Mode Decision Briefs

## Transition 1: MAINTENANCE → WORK (2026-11-24T12:00:00)

At 2026-11-24T12:00:00Z, the fleet transitioned from MAINTENANCE to WORK. At the time of the change, 0.0% of tracked goals were complete. The trigger was: a new work cycle was initiated with fresh goals. The fleet will remain in WORK (active goal-pursuit mode where all agents work their open goals) until the next transition condition is met. All agents will resume working their open goals from the next10.json dispatch queue on the next pass cycle.

## Transition 2: WORK → MAINTENANCE (2026-11-24T08:00:00)

At 2026-11-24T08:00:00Z, the fleet transitioned from WORK to MAINTENANCE. At the time of the change, 95.0% of tracked goals were complete. The trigger was: the current work cycle completed its closeout sequence. The fleet will remain in MAINTENANCE (maintenance mode where agents perform scheduled upkeep tasks instead of new goals) until the next transition condition is met. Agents will switch to role-specific maintenance tasks from the idle-rotation table; new goal work is paused until re-entry to WORK mode.
