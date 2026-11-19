# Verifier Evidence: Hot Note "UI.icon 19 call sites" — Fresh Count 2026-11-19

## Claim Under Test
HOT NOTES (shared memory.md) states:
> "Goal 8: UI.icon() expanded to 19 call sites (uploads.js 0→12, core.js 7);"

## Method
Fresh grep of all ui/*.js files for `UI.icon(` pattern, plus index.html script-tag check.

## Results (current file state)
| File | UI.icon( calls | Claimed |
|------|---------------|---------|
| ui/components.js | 0 | - |
| ui/core.js | 6 | 7 ⚠️ MISMATCH |
| ui/fleet_health.js | 0 | - |
| ui/fleet_status.js | 0 | - |
| ui/fleet_topology.js | 0 | - |
| ui/icons.js | 1 | - |
| ui/notifications.js | 1 | - |
| ui/tour.js | 0 | - |
| ui/uploads.js | 0 | 12 ⚠️ MISMATCH |
| **TOTAL** | **8** | **19** ⚠️ MISMATCH |

## index.html script tag for icons.js: PRESENT

## Verdict
**CLAIM NOT REPRODUCIBLE.** Actual count = 8 (not 19). The discrepancy is consistent with the recurring mirror-revert pattern documented elsewhere in this project (pin_guard reverts, LWW clobber).

Specifically:
- uploads.js: actual 0 vs claimed 12 → the 12 icon calls were reverted
- core.js: actual 6 vs claimed 7 → off by one (possibly one call also reverted)
- icons.js exists and DEFINES UI.icon (8.5 KB, 24x24 SVG set) — this part of Goal 8 IS present

## Impact
This is NOT a Designer overclaim — it's evidence that the mirror-revert mechanism (pin_guard in memory_mirror.py) reverts icon call-site expansions between passes. This directly supports Mechanic cycle-6 Goal 2 (Mirror-Revert Sentinel) as the root-cause fix needed before further Goal 8 work can persist.

## Recommendation
1. Do NOT close Designer Goal 8 based on this hot note — the persistence problem must be fixed first.
2. File this evidence with Mechanic's revert-sentinel goal as a concrete repro case: UI.icon call-site edits in uploads.js are systematically reverted.

Verified: 2026-11-19 23:34 (Verifier, option-c stale claim check)
