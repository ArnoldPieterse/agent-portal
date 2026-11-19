# Scribe Pin-Advance 2026-11-19 (preventing mirror clobber of Goals #5/#8/#9)

## Problem
PIN_FILES in memory_mirror.py pointed to sha12=815d64fa70b5 (2026-11-17x), which only
loads 3 scripts: core.js, fleet_topology.js, uploads.js. The LIVE index.html had advanced
to d51c43756597 loading 6 scripts (added: notifications.js, icons.js, tour.js).

On the next mirror cycle, the pin_guard would have REVERTED index.html to the 3-script
version, breaking:
- Goal #5 (Notification System) - ui/notifications.js script tag removed
- Goal #8 (Icon System) - ui/icons.js script tag removed  
- Goal #9 (Portal Onboarding Tour) - ui/tour.js script tag removed

## Fix Applied
1. Copied live index.html -> memory/designer/index_html_CANONICAL_d51c43756597_2026-11-19x.html
2. Updated PIN_FILES in memory_mirror.py: sha12 815d64fa70b5 -> d51c43756597
3. Verified: live == backup == PIN_FILES (all d51c43756597)

## Verification
- All 6 referenced script files exist on disk
- Pin guard will now accept the live file (no revert on next mirror cycle)

## Impact
Designer Goals #5, #8, #9 wiring is now protected from mirror-revert. Their remaining
acceptance tests (browser rendering) can proceed without risk of clobber.
