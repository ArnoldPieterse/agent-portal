# Goal 5 + QA Gate: Scale compliance fixed
Date: 2026-11-20
Action: design_qa.py found 3 failures (off-scale fs tokens 11/13/16, off-scale gaps 6px/18px).
Fixes applied:
- ui/tokens.css: removed --fs-11, --fs-13, --fs-16; kept canonical 5-step scale (12/14/15/18/24)
- ui/app.css: var(--fs-13)->var(--fs-14), var(--fs-11)->var(--fs-12); gap:6px->gap:8px (x3), gap:18px->gap:16px
Result: python memory/designer/design_qa.py = 12/12 PASS, exit 0
