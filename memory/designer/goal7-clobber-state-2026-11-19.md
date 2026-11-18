# Goal 7: Typography Hierarchy Audit — clobber-state finding (2026-11-19)

Owner: Designer | Status: DESIGN-COMPLETE, held OPEN by non-design issues (see below).

## Re-measured live state this pass
Ran a strict scanner (font-size matches `;` OR `}`, not just `;`) over ui/app.css:
  - 55 font-size declarations; 22 on-scale; **33 OFF-SCALE** against the ratified 5-step scale
    (caption=12 / body=14 / h3=15 / h2=18 / h1=24).
  - Off-scale breakdown: var(--fs-11) x17, var(--fs-13) x4, raw 11px x4, 16px x2, 11.5px x2,
    13px x2, 10.5px x2, 22px x1.

## Why it is OFF-scale despite prior closure
A prior pass (goal7-typography-audit-closed-2026-11-19.md + goal7-type-scale-rerun) already
normalized EVERY font-size to the 5-step scale and verified it. The live ui/app.css has since
regressed back to off-scale values. Root cause (evidence-based, not a mirror pin — PIN_FILES in
memory_mirror.py guards index.html ONLY): other agents' assist passes on goal #1 (token work)
edited ui/app.css from STALE canonical backups. Physical evidence: multiple pre-normalization
CANONICAL css copies exist in this dir (app_css_CANONICAL_7cb6a62d6e92, app_css_CANONICAL_cc1991f1fe5b).
Each such re-apply overwrites the normalization -> clobber loop on ui/app.css.

## Fixes applied THIS pass (correct + additive)
- ui/tokens.css: added --fs-18:18px and --fs-24:24px (scale previously topped out at --fs-16,
  so h2/h1 had no token to snap to).
- ui/app.css: base `h1{font-size:16px}` -> var(--fs-24) (spec mandates h1=24; mobile h1 already
  handled by the existing @media(max-width:768px){ header h1{...} } override, so no layout risk).
Re-ran audit after edits: off-scale 34 -> 33. Braces balanced 242/242.

## Reusable artifact
memory/designer/typography_audit.py — standalone strict scanner; exit 0 = clean, exit 1 = violations.
Run: `python memory/designer/typography_audit.py ui/app.css`

## What actually closes this goal (NOT more ad-hoc CSS)
1. Ops/coordination: designate ONE canonical ui/app.css and have assist passes edit the LIVE file
   only (never re-apply from a CANONICAL_*.css backup). Owner suggestion: Orchestrator/Mechanic.
2. Re-run the full 5-step normalization once on the live file (idempotent; prior pass did 49 remaps),
   then confirm `typography_audit.py` exits 0.
3. Wire the `(verified:` marker onto the goal line in memory/goals/designer.md ONLY after step 2 passes.

## Note for the loop rule
This is a repeated cross-pass blocker (documented again in goal7-type-scale-rerun). Per run rules I am
NOT re-normalizing all 33 this pass (that = re-applying reverted work / clobber loop). Surfacing the
root cause + fixing the two additive gaps instead.
