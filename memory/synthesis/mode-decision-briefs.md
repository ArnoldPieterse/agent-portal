# Mode Decision Briefs

Regenerated: 2026-11-24T10:43:52+00:00 | transitions on file: 5

## Transition 1

At 2026-11-24T08:00:00Z the fleet moved WORK -> MAINTENANCE. At that moment: cycle_closeout. Decision: all goals reached 100% while the fleet was still active, opening the maintenance window. Fleet mode follows three rules: WORK while any goal is open (pct < 100); MAINTENANCE once all goals are reached but the fleet was active within the last 6 hours; IDLE after 6 quiet hours.

## Transition 2

At 2026-11-24T12:00:00Z the fleet moved MAINTENANCE -> WORK. At that moment: new_cycle_start. Decision: open goals were re-detected, overriding the maintenance window. Fleet mode follows three rules: WORK while any goal is open (pct < 100); MAINTENANCE once all goals are reached but the fleet was active within the last 6 hours; IDLE after 6 quiet hours.

## Transition 3

At 2026-11-24T01:09:29.276602+00:00 the fleet moved IDLE -> WORK. At that moment: goal_pct=30.0, elapsed=0.01h; 56 goal(s) still open. Decision: activity resumed and open goals were detected, so the fleet returns to goal work. Fleet mode follows three rules: WORK while any goal is open (pct < 100); MAINTENANCE once all goals are reached but the fleet was active within the last 6 hours; IDLE after 6 quiet hours.

## Transition 4

At 2026-11-24T10:37:02.445560+00:00 the fleet moved IDLE -> WORK. At that moment: goal_pct=63.7, elapsed=0.0h; 29 goal(s) still open. Decision: activity resumed and open goals were detected, so the fleet returns to goal work. Fleet mode follows three rules: WORK while any goal is open (pct < 100); MAINTENANCE once all goals are reached but the fleet was active within the last 6 hours; IDLE after 6 quiet hours.

## Transition 5

At 2026-11-24T10:37:07.415832+00:00 the fleet moved IDLE -> WORK. At that moment: no metrics captured at transition time. Decision: activity resumed and open goals were detected, so the fleet returns to goal work. Fleet mode follows three rules: WORK while any goal is open (pct < 100); MAINTENANCE once all goals are reached but the fleet was active within the last 6 hours; IDLE after 6 quiet hours.
