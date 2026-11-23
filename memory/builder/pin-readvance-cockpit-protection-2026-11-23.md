# Pin Re-Advance + Cockpit.js Protection (Builder assist)
Date: 2026-11-23

## Problem
PIN_FILES in memory_mirror.py was stale (sha12=64f12eb4c16a, dated 2026-11-22).
The live index.html had drifted to sha12=a00d6ac0083d (includes ui/cockpit.js + ui/scheduler.js).
If the mirror cycle ran before pin was advanced, cockpit.js and scheduler.js script tags
would be reverted, breaking the Fleet Cockpit tab.

## Fix
1. Computed current sha12: a00d6ac0083d
2. Wrote backup: memory/designer/index_html_CANONICAL_a00d6ac0083d_2026-11-23b.html
3. Updated PIN_FILES in memory_mirror.py (sha12 + backup path)

## Verification
- Pin sha matches live file: PASS
- Backup file exists: PASS
- ui/cockpit.js referenced in index.html: PASS

## Impact
Cockpit tab and scheduler now protected from mirror revert. Closes Verifier's stale
finding "cockpit-js-not-loaded" (the tag IS present; pin was just lagging).
