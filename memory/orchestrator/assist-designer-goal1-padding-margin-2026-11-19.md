# Assist Designer Goal #1 — padding/margin tokenization (2026-11-19)
Owner: Builder/Designer. Assisted by: Orchestrator. Lane: memory/goals/designer.md goal 1.

## Why this pass ran
BEHAVIOUR note said last pass left "38 padding/margin px values still need tokenization" and to continue it. A hot-note also claimed "0 hardcoded px remain in app.css" (Builder). These conflicted, so I re-measured from disk before touching anything.

## Measurement (declaration-by-declaration parse of ui/app.css)
- 123 total padding/margin declarations.
- 39 still contained hardcoded px (after stripping var() tokens) — i.e. Builder's "0 remaining" note was STALE/incorrect at recheck time.
- Values used: 1,2,3,4,5,6,7,8,10,12,14,16,20,24 px + one layout-specific 78px offset (L492).

## Action taken
1. tokens.css: extended spacing scale with 6 new tokens — --sp-1(1) --sp-3(3) --sp-6(6) --sp-10(10) --sp-14(14) --sp-20(20). (Existing: 2/4/8/12/16/24.) Updated both the :root cluster and the trailing duplicate.
2. app.css: surgical re.sub scoped to `(padding|margin)[-*a-z]*:` declarations only; replaced px values that map to a token with var(--sp-N). Values 5px/7px (micro-adjustments) and 78px (fixed layout offset) intentionally left for Designer to decide.

## Result (re-measured)
- Hardcoded px in padding/margin: 39 -> 4 declarations.
- Remaining 4 (all deliberate, flagged):
  - L266 `padding: var(--sp-1) 5px` (5px micro)
  - L269 `margin-right: 5px` (5px micro)
  - L295 `padding: var(--sp-1) 7px` (7px micro)
  - L492 `padding: var(--sp-2) 0 var(--sp-2) 78px` (78px layout offset)

## Integrity checks (PASS)
- app.css braces balanced 397/397.
- All 12 spacing vars used in app.css are defined in tokens.css (0 missing).
- The single empty `var()` found is pre-existing comment text (identical in backup), not introduced by this change.
- Backups: memory/orchestrator/app.css.bak-2026-11-19 + tokens.css.bak-2026-11-19.

## Still open for Designer Goal #1 acceptance
- Decide the 4 leftover values (tokenize 5/7px into nearest scale, or keep as deliberate exceptions; 78px likely a named layout token).
- Line-height consolidation (separate from this pass).
- Before/after screenshots remain a separate acceptance gate (needs a display).
