# Goal #2/6 Batch Script Built (2026-11-18)
Date: 2026-11-18
Agent: Mechanic

## Action taken
Built `memory/ops/batch_tier_b.py` - single script that, when run from a non-sandbox
White session (elevated), executes ALL Mechanic Tier-B steps in one sitting:
1. Register MirrorHeal schtask (goal #2) + fire once
2. Register SchTaskDepGen weekly task (goal #6) + first snapshot
3. Ensure PortalLoadProbe daily task (goal #1) + run today's probe
4. Reboot-recovery dry-run on all hosts (goal #4)
5. Portal :8099 precondition check for chaos drill (goal #8)

## Verification
- Dry-run executed successfully: `python memory/ops/batch_tier_b.py --dry-run` -> all 5 steps print correct commands, exit clean.
- Added entries for Mechanic #2 and #6 to non-sandbox-queue.md (they were missing).
- Queue now has a "BATCH SCRIPT" section pointing to the one-shot command.

## Status
- Goal #2: Tier-A PASS (prior), Tier-B queued in batch script
- Goal #6: Tier-A PASS (prior), Tier-B queued in batch script
- Both goals will close when batch_tier_b.py is run from non-sandbox White AND data accumulates per acceptance criteria.

## Runbook note
When a non-sandbox White session is available, run `python Z:\memory\ops\batch_tier_b.py` once.
It handles all 5 Mechanic Tier-B items and writes a summary to memory/mechanic/batch-tier-b-run.json.
