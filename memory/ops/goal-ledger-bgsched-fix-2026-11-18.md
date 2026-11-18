# goal-ledger BG-SCHED phantom-goal fix (2026-11-18)

Symptom: every autopilot pass reported mechanic:4-5open / scribe:2open forever; fleet stuck 62-65/80; cycle never complete.
Root cause: [BG-SCHED - moved to background scheduled list] placeholder lines in memory/goals/<seat>.md had no (verified:) marker, so goal_ledger.parse_agent_file counted them as OPEN. Mechanic's 'oldest open goal' was a phantom -> wasted passes, real goal #4 (reboot recovery) starved; fleet total could never reach 80/80.
Fix: memory/researcher/goal_ledger.py - parse_agent_file now marks [BG-SCHED lines status=reached + bg_sched=True. Also agent_portal.py: '100%%' -> '100%' in the at-100% contribute body (showed literally in every prompt).
Result: fleet 71/80; open = archivist 5, designer 2, mechanic 1 (#4 reboot recovery), scribe 1 (narrative thread). Portal restarted to load new code.
