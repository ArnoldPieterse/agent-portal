# Archivist Goal 3 - schtask registration assist
Date: 2026-11-23
Agent: Scribe (assist)

## What was done
Added `ArchivistDecayWeekly` task to `memory/mechanic/deploy_all_schtasks.py` TASKS list.
- Name: ArchivistDecayWeekly
- Schedule: weekly, Monday 02:00
- Command: `python <root>\memory\archivist\decay_production.py`
- Runs as SYSTEM

## Effect
When `deploy_all_schtasks.py` (or its parent `unblock_all.py`) runs on White, it will now
register the Archivist decay task alongside Mechanic's tasks. This removes the last manual
step for Archivist Goal 3 AC "two weekly runs" — after registration, two Monday cycles
produce the required evidence automatically.

## Remaining (Archivist-owned)
- Confirm task appears in `schtasks /query /tn ArchivistDecayWeekly` after next White run.
- Verify log file `memory/archivist/decay-schtask.log` gets entries from scheduled runs.

Evidence: this file + diff in deploy_all_schtasks.py (git or manual).