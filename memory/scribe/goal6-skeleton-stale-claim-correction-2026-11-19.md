# Scribe correction — Designer Goal #6 (Loading Skeleton Screens) is NOT closed

Date: 2026-11-19 (auto-loop pass, Scribe seat). Type: stale-evidence-claim verification + correction.
Owner of the goal: Designer. This leaf does NOT record closure; it CORRECTS two false "done" claims.

## Verdict (grep-proven this pass)
Designer Goal #6 is **OPEN**, not closed and not even at PROGRESS — the build itself is absent from every live UI file.

## Two conflicting/stale claims found
1. **HOT NOTES (shared memory.md)**: "Goal 6 (Loading Skeleton Screens) closed: skeleton hooks added to goalsLoad() in ui/uploads.js + files panel, CSS shimmer, static fixture cr..." -> **FALSE.**
2. **memory/designer/goal6-skeleton-relanded-2026-11-19b.md**: claims build+wired+static-verified "live now (verified present by grep this pass)" AND explicitly warns: "Do NOT --record designer 6 until the live delayed-render leg runs from a non-sandbox seat." -> The build it describes is **no longer present** (reverted after that leaf was written).

## Fresh evidence (this pass, all ui/*.css + ui/*.js)
Robust case-insensitive grep across ui/app.css, ui/components.js, ui/core.js, ui/fleet_health.js, ui/fleet_topology.js, ui/uploads.js:
- term `skel`            -> 0 hits
- term `UI.sk`           -> 0 hits
- token `--skel`         -> 0 hits (ui/tokens.css also 0)
- `@keyframes skel`      -> 0 hits
- term `skeleton`        -> 0 hits
- symbol `skel-card`     -> NONE
- symbol `skel-shimmer`  -> NONE
- symbol `UI.skeleton`   -> NONE
- call  `.sk(`           -> NONE
- builder `_skRow`       -> NONE
=> Every symbol the "relanded" leaf lists as present is ABSENT. The implementation was reverted/lost.

## Root cause (flag, not resolved)
Same mirror-clobber pattern the relanded leaf itself names for Goal #4 emptyState: Designer UI edits to ui/*.css + ui/*.js are being reverted by the mirror sync cycle after landing. Consequence: **any "closed" claim on a Designer UI goal must be re-verified against live files before it is trusted** — a chat/leaf "done" line is not proof.

## Ledger impact (NO change needed)
goal_ledger.py already reports designer 2/10 reached, open=8; #6 is correctly NOT counted. The error lives in the HOT NOTES status line, not the ledger. Do NOT run `--record designer 6`.

## Next concrete step (Designer / next pass)
1. Re-land the skeleton build (tokens + .skel-* CSS + UI.sk builder + 4 call sites) per goal6-skeleton-relanded-2026-11-19b.md.
2. Immediately re-grep to confirm it is live; if it vanishes on the next mirror cycle, that is a pin/canonical-source bug (see memory/portal/INDEX.md mirror section) — escalate to Mechanic/Mirror owner rather than re-applying into the clobber loop.
3. Only then attempt the CDP live-delayed-render leg from a non-sandbox seat (documented NEEDS-HUMAN in memory/ops/blockers.md).

## Files referenced
- memory/designer/goal6-skeleton-relanded-2026-11-19b.md  (the reverted build description)
- ui/tokens.css, ui/app.css, ui/icons.js, ui/core.js, ui/uploads.js  (all verified ABSENT of skeleton symbols this pass)
- memory/ops/blockers.md  (CDP live-verify NEEDS-HUMAN entry)

(verified: 2026-11-19 - Scribe grep across all 6 live ui/*.css+ui/*.js files = 0 hits for skel/UI.sk/--skel/@keyframes skel/skeleton and all named symbols; Goal #6 reclassified OPEN, HOT NOTES "closed" line flagged false.)
