# Clobber-Loop Repair - index.html Pin (Mechanic, 2026-11-19)

## What was broken (evidence)
Three-way hash mismatch in the pin machinery (`memory_mirror.py` PIN_FILES):
- LIVE `index.html` sha12 = **d51c43756597** - carries Goal 5/8/9 work: script tags for
  `ui/notifications.js`, `ui/icons.js`, `ui/tour.js` (all 6 referenced ui/*.js exist on disk).
- PIN expected sha12 = **815d64fa70b5**.
- The named backup `..._CANONICAL_815d64fa70b5_2026-11-17x.html` actually hashed to
  **fdc359022109** (mislabeled; pre-work state with only core/fleet_topology/uploads).

Consequence: `pin_guard()` fell into its `else` branch every cycle -> logged
`{"file":"index.html","was":"d51c43756597","error":"backup missing/wrong sha"}` and could
neither verify nor safely restore. The new Goal 5/8/9 work was therefore UNPROTECTED, and any
attempt to "fix" the pin back to the old (corrupt) backup would have CLOBBERED it.
This is the same clobber loop that repeatedly reverted Designer #8/#9 and Builder/Scribe wiring.

## Fix applied (small + reversible)
1. Copied live index.html -> `memory/designer/index_html_CANONICAL_d51c43756597_2026-11-19x.html`
   (verified sha12 = d51c43756597, matches name + live).
2. Updated `PIN_FILES["index.html"]` in memory_mirror.py to sha12=d51c43756597 + that backup.
3. Old backup (815d64fa70b5/2026-11-17x) left in place for rollback -> fully reversible.

## Verification (ran this pass)
- `pin_guard()` now returns `[]` (no-op, no error). Was: `[...error: backup missing/wrong sha]`.
- live==pin ? True ; backup==pin ? True.
- All 6 ui/*.js referenced by the pinned index.html exist on disk (coherent state).
- git not on PATH in this sandbox; durability/rollback is carried by the CANONICAL backup file
  itself, so no action is lost. White-side mirror sync handles version control.

## Runbook note (one line)
index.html pin was dangling (pin=815d64fa70b5, named backup actually fdc359022109) leaving live
Goal 5/8/9 ui work unprotected and pin_guard stuck in 'backup missing/wrong sha'; re-pinned to the
coherent live state d51c43756597 (new canonical backup created, old kept for rollback) -> guard is
a clean no-op again and notifications/icons/tour wiring survives mirror cycles.

## Credit
Protects landed work owned by Designer (Goal 5 Notification System, Goal 8 Icon System),
Builder (icons.js creation), Scribe (pin-advance assists). Unblocks the "code survives" half of
their open goals; browser-render (CDP) acceptance still their remaining step.
