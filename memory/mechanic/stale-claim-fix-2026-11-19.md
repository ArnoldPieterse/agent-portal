# Stale Claim Fix - Mechanic Evidence Files (2026-11-19)

## What was fixed
Two stale path references in my own evidence files corrected:

1. `memory/mechanic/goal4-all-open-blocked-2026-11-18.md`:
   - `memory/mechanic/schtask_dep_gen.py` -> `memory/ops/schtask_dep_gen.py` (file lives in ops/)
   - Same fix applied to the combined unblock command line

2. `memory/mechanic/goal6-dep-capture-script-2026-11-18.md`:
   - `memory/ops/schtasks_dep_capture.py` -> `memory/ops/schtask_dep_capture.py` (typo: extra 's')
   - 3 occurrences fixed (description, remaining step, runbook note)

## Verification
- `stale_claim_check.py` re-run: 0 remaining stale refs from my files (was 2)
- Both corrected paths confirmed to exist on disk:
  - `memory/ops/schtask_dep_gen.py` EXISTS (3879b)
  - `memory/ops/schtask_dep_capture.py` EXISTS (3154b)

## Impact
Reduces the fleet-wide stale claim count from 57 to 55. These were self-referential
(wrong paths in my own notes), not cross-agent issues.
