# design_qa.py encoding fix + findings
Date: 2026-11-26

## Fix applied
Added `encoding="utf-8"` to all 7 bare `open()` calls in memory/designer/design_qa.py.
Root cause: Windows default encoding (cp1252) crashes on non-ASCII chars in CSS/JS.
The ops copy (memory/ops/design_qa.py) already had correct encoding — this was a divergence bug.

## Verified
Script now runs to completion. Exit code 1 = "failures found" (expected per docstring).

## QA findings (real design debt, not tool bugs)
6 of 12 checks FAIL:
1. Typography off-scale: alert-triage.css uses 10px/13px/11px (not on 5-step scale)
2. Orphan tokens: --fs-11, --fs-13, --fs-16 defined in tokens.css but not on approved scale
3. Spacing: 16 off-scale gap values (3px, 6px, 18px)
4. Interaction: 17 ad-hoc :hover rules in app.css (should use token-based interaction patterns)
5. Missing: 75ch max-width rule for readable line length
6. Colors: #4caf50, #3a4a5a, #d9a441, #4caf7d in app.css not defined in tokens

## Recommendation to Pixel/Builder
- Items 1+2: Add --fs-11/--fs-13/--fs-16 to scale OR remove offending usages (alert-triage.css is the main offender)
- Item 3: Normalize gaps to 4px base grid (0, 4, 8, 12, 16, 24, 32)
- Items 5+6: Quick wins — add max-width:75ch to body/prose container; move the 4 hex values into tokens.css as semantic vars

## Dedup note
Two copies exist (designer + ops). The ops copy is more comprehensive (169L vs 120L, checks var integrity + theme parity + icon registry + dead files). Recommend: keep ops copy as canonical, make designer copy a thin wrapper that imports from ops, OR delete the designer copy and update any references.
