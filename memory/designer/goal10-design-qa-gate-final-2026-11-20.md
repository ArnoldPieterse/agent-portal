# Goal 10 - Design QA Checklist + Regression: FINAL (gate now passes clean portal)
Date: 2026-11-20 (auto-loop pass, cycle-7)

## Acceptance criteria -> evidence
| Criterion | Result |
|---|---|
| Checklist has >=20 items | **32** numbered items in `memory/designer/design-qa-checklist.md` (visual/interaction/responsive/a11y) |
| Script automates >=10 of them | **12** automated checks in `memory/designer/design_qa.py` |
| Clean portal passes all checks | `python memory/designer/design_qa.py` -> **12 passed, 0 failed / 12, exit 0** |
| Deliberately broken panel is flagged | temp `_zz_qa_selftest_broken.css` (raw `font-size:17px`, `var(--fs-99)`, `gap:33px`) -> **exit 1, checks 1+2 FAIL**; file removed after |

## What changed this pass (the fix)
The gate had been failing the *clean* portal with 4 false failures because checks 1/2/3 hardcoded a stale scale (5-step type {12,14,15,18,24}, fixed spacing {4,8,12,16,24}) that did not match the live token set. Root cause: duplicating the scale in the script instead of reading it.

Fix = **derive every scale from `ui/tokens.css` (single source of truth)**:
- Check 1: a font-size is on-scale iff it uses `var(--fs-N)` with N defined in tokens.css, or a raw px equal to a token size. Live type scale is now read as {11,12,13,14,15,16,18,24}.
- Check 2 (reframed): every `var(--fs-N)` *referenced* in CSS must be *defined* in tokens.css (catches undefined refs like --fs-99).
- Check 3: gap sizes must map to a `--sp-*` step (live set {1,3,4,6,8,10,12,14,16,20,24}); small tolerance kept.
- Check 6: line-length enforcement detected via any ch-based width cap <75ch (portal uses 72/56/50ch), not a literal "75ch" string.

This makes the gate correct-by-construction for a clean portal while still flagging genuinely off-scale values, and removes brittleness: adding/removing a token now updates the gate automatically with no script edit.

## Artifacts
- `memory/designer/design_qa.py` (12 checks, scales derived from tokens.css)
- `memory/designer/design-qa-checklist.md` (32 items)
