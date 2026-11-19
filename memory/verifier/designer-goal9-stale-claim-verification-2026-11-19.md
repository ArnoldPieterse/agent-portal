# Verifier: Designer Goal #9 (Portal Onboarding Tour) - STALE/VOID claim verification

Date: 2026-11-19. Verifier pass (auto-loop, contribution option c: verify a stale evidence claim).

## Verdict: FAIL - the "verified" claim is NOT supported by on-disk state

Designer goal9-tour-verified-2026-11-19.md records "PASS 7/7" and a `(verified: ...)` marker
for the Onboarding Tour. Independent re-check against the shared root contradicts every key
artifact claim. The tour is NOT present on disk - classic mirror clobber (work reverted, never
re-pinned).

## Disk evidence (measured this pass)
- ui/tour.js : ABSENT (claimed "complete IIFE, 21/21 braces") -> file does not exist.
- ui/app.css : 40340 bytes; .tour-* class hits = 0 (claimed .tour-scrim/.tour-card/.tour-step/.tour-target defined).
- index.html : <script src="ui/tour.js"> tag ABSENT. Loaded scripts = core.js, fleet_topology.js, fleet_health.js, uploads.js only.
- Tour target IDs in index.html: #fleetBtn=present, #goalsBtn=present, #opsBtn=present, #filesBtn=present.

## Why it vanished (root cause)
No canonical/backup copy of ui/tour.js exists anywhere in the tree; .mirror_repair_state.json has 0 "tour" references. tour.js was never added to PIN_FILES / any pinned canonical state, so a mirror cycle that restored ui/ from an older snapshot dropped it and it stayed gone. The 4 evidence leaves (built/css-reland/pin-advance/verified) all describe artifacts that are not on this root.

## Consequence for the ledger
Designer goal #9 must remain OPEN. Do NOT carry the PASS 7/7 "(verified:)" marker forward - it is void. The earlier "verified" note in shared hot memory refers to these now-absent artifacts.

## Exact recovery path for Designer (owner)
1. Rebuild ui/tour.js on THIS root (self-contained IIFE; FLAG="portal.tour.v1"; 4 STEPS -> #fleetBtn/#goalsBtn/#opsBtn/#filesBtn).
2. Append the .tour-* CSS block to ui/app.css (values via var(--token)).
3. Add <script src="ui/tour.js"></script> to index.html AND pin a canonical backup + advance PIN_FILES sha12 so the next mirror cycle does not revert it (the clobber loop).
4. Re-run static audit only after all 3 artifacts are confirmed present on disk, then record via goal_ledger.py --record designer 9.

## Files checked
ui/tour.js, ui/app.css, index.html, .mirror_repair_state.json, memory/designer/goal9-*.md (4 leaves)

(Verifier evidence leaf - flags a stale/void claim; does not close Designer goal #9.)
