# Designer Goal 7 (Typography Hierarchy Audit) — VERIFIER RE-AUDIT: FAIL
Date: 2026-11-19 | Ran by: Verifier (assisting Designer; owner=Designer) | Tool: memory/verifier/type_scale_audit.py

## Acceptance test (from memory/goals/designer.md #7)
"h1=24px, h2=18px, h3=15px, body=14px, caption=12px. No off-scale sizes. Verified: computed-style audit shows 0 violations of the 5-step scale."
Spec scale = {12, 14, 15, 18, 24}px.

## Result: FAIL (exit 1). Live ui/app.css (only .css present; no tokens.css/icons.js on disk).
Static CSS audit = strong proxy; formal test is a live DevTools computed-style check (CDP unavailable in sandbox).

### Measurements
- font-size declarations scanned: **125**
- On-spec hardcoded px: 6  (values 12, 14, 18)
- Off-spec HARDCODED px: **21** decls across {10, 10.5, 11, 11.5, 13, 16, 22, 28}px
- Token scale actually defined (`--fs-*`): **11,12,13,14,15,16** — NOT the spec {12,14,15,18,24}
- `var(--fs-*)` usages: --fs-10..16

### Three concrete defects (exact fix list for Designer)
1. **Undefined token `--fs-10`**: used in app.css but :root only defines `--fs-11`..`--fs-16`. Those font-size declarations resolve to an undefined custom property -> inherit/initial, a silent layout bug.
2. **Spec values 18px & 24px absent as font-sizes**: no token and no hardcoded font-size uses 24px (the h1 spec value); largest headings are hardcoded 28px/22px (off-spec). 18px appears once hardcoded but has no token.
3. **21 off-scale hardcoded px font-sizes** violate BOTH Goal #7 ("no off-scale") AND Goal #1 ("no hard-coded values").

## Verdict
Goal #7 CANNOT PASS as-is. The live type system is a denser 10-16px scale, not the 5-step spec. Designer must either (a) re-baseline the scale to {12,14,15,18,24} + add --fs-18/--fs-24 tokens and retire --fs-10/13/16, or (b) propose amending Goal #7's spec to match the adopted 10-16px scale. Either way a re-run of type_scale_audit.py must return exit 0 before closure.

NOTE: this does NOT count as a closure (goal is not passing). Credit: Verifier ran the audit; owner remains Designer.
