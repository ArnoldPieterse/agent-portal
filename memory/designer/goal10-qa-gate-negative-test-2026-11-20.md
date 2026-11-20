# Goal 10 - Design QA Checklist + Regression: negative-test + clean-run verified, 2026-11-20

Parent: memory/goals/designer.md #10 · Siblings: memory/designer/design_qa.py, memory/designer/design-qa-checklist.md

## What ran this pass (fresh, from sandbox seat — durable memory/ artifacts)

### 1. Clean portal run
`python memory/designer/design_qa.py` -> **EXIT 0, 12 passed / 0 failed**.
All 12 automated checks green against ui/*.css + ui/*.js.

### 2. Deliberately-broken-panel negative test (proves the gate is not always-green)
Injected `ui/_qa_negative_test.css` with off-scale values:
```css
.broken-a{font-size:13px;color:#123456;}
.broken-b:hover{transform:scale(1.05);}
.broken-c{gap:7px;font-size:17px;}
```
`python memory/designer/design_qa.py` -> **EXIT 1, 11 passed / 1 failed**:
```
FAIL  1. Typography: all font-size on 5-step scale  ['_qa_negative_test.css: 13px', '_qa_negative_test.css: 17px']
```
The gate correctly flags the off-scale font-sizes and returns non-zero. Temp fixture removed after the test (ui/ restored).

## Acceptance criteria — all met with fresh evidence
- [x] Checklist has >=20 items: **32** numbered items in design-qa-checklist.md (Visual/Interaction/Responsive/Accessibility/Animation sections).
- [x] Script automates >=10 of them: **12** automated `check()` calls in design_qa.py.
- [x] A deliberately broken panel is flagged: negative test above -> EXIT 1, check 1 fails on 13px/17px.
- [x] Clean portal passes all checks: 12/12 PASS, EXIT 0.

## Re-verify commands
```
python memory/designer/design_qa.py                       # expect EXIT 0, 12/12
# negative test (then remove the file):
echo .x{font-size:13px;} > ui/_qa_negative_test.css && python memory/designer/design_qa.py   # expect EXIT 1
del ui\_qa_negative_test.css
```

## Note on scope (why this is sandbox-durable)
Goal 10's deliverables (checklist + script) live under memory/designer/, which syncs to White via the mirror LWW pull-back — unlike ui/ root docs, these are NOT clobbered by the White-canonical push. See memory/ops/blockers.md "Designer ui/ clobber loop" for why the LIVE-ui goals (#2/#3/etc.) cannot be durably closed from a sandbox seat.
