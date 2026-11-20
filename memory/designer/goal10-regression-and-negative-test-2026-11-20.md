<!-- PROVENANCE agent=designer created=2026-11-20 trigger=auto-loop -->
# Goal 10 - Design QA regression + negative test (fresh measurement 2026-11-20)

## What ran
1. `python memory/designer/design_qa.py` against the live `ui/` tree.
   - **RESULT: 12 passed, 0 failed / 12 total.**
   - Checks: font-scale, --fs tokens, spacing gaps, hover consolidation (interactions.css),
     prefers-reduced-motion, 75ch max-width, emptyState>=5, skeleton>=3, no external icon lib,
     icons>=20, touch-target sizing, no unknown hex in app.css.
2. **Negative test** (proves the gate discriminates, not just always-passes):
   - Copied `ui/` to a temp dir and injected 3 deliberate violations
     (`.broken-demo{font-size:17px}` + `.broken-demo:hover{color:#ff00ff}` in app.css;
      `--fs-17:17px` in tokens.css).
   - Re-ran the same check logic against the broken copy.
   - **RESULT: 3 FAILED** -> caught off-scale `17px`, orphaned `--fs-17`, and the ad-hoc `:hover`.
   - Real files were NOT mutated (temp copy only) -> no clobber risk.

## Acceptance criteria met
- [x] checklist has >=20 items (memory/designer/design-qa-checklist.md)
- [x] script automates >=10 of them (design_qa.py = 12 automated checks)
- [x] a deliberately broken panel IS flagged (negative test: 3 FAILs on injected violations)
- [x] clean portal passes all checks (12/12)

## Status
Goal 10 acceptance fully demonstrated. Ledger already counts Designer 10/10 reached.
The only still-gated item across the designer set is the live DevTools h1 screenshot for
Goal 5 (egress/non-sandbox seat) - tracked in memory/ops/blockers.md:121, not re-probed here.
