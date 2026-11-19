# Goal #1 (Design Token System) — spacing tokenization complete, 2026-11-19

Owner: Designer. Auto-loop pass (oldest open goal).

## What was left
Goal #1's strict acceptance leg (hex colors in ui/*.css = 0) already passed (Verifier assist).
The tracked residual from the prior PROGRESS note was: "decide token vs keep for the 5px/7px/78px
leftovers + before/after screenshots." The screenshot leg is the shared browser blocker already
recorded in memory/ops/blockers.md (do NOT re-probe). This pass resolves the spacing-decision leg.

## Decision + change (ui/app.css)
Spacing scale = 1/2/3/4/6/8/10/12/14/16/20/24 (--sp-*). Every residual micro value had a token
within 1px, so I snapped on-scale rather than adding bloat tokens (keeps the scale tight):
- L245 `code` horizontal padding 5px -> var(--sp-6); border-radius:5px -> var(--br-sm)
- L248 `.legend i` margin-right 5px -> var(--sp-6)
- L274 `.ft-chip` horizontal padding 7px -> var(--sp-8)
- gap sweep (6): 6px x3 -> var(--sp-6); 4px x2 -> var(--sp-4); legend 18px -> var(--sp-16)
  (tightened 2px, consistent with the Information Density Pass goal #2 direction)

## Verification (static; browser leg blocked per blockers.md)
- braces balanced 317/317
- var() refs used: 68; undefined tokens: NONE
- hardcoded px in padding/margin/gap props: 0 (was 9 before this pass)
- hex colors in app.css: 0

## State
Spacing tokenization now complete. Goal #1 remaining = browser before/after screenshots only
(shared blocker, already NEEDS-HUMAN-reconciled in memory/ops/blockers.md). Not re-probing.
