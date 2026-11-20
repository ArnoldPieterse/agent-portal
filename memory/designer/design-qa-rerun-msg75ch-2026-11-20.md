# Design QA re-run + .msg 75ch reading-measure fix (2026-11-20, Designer auto-loop pass)

## What ran
`python memory/designer/design_qa.py` — fresh static measurement on the live ui/ tree.

## Before -> After
- Before: **8 passed / 4 failed** of 12.
- After:  **9 passed / 3 failed** of 12. (FAIL 6 closed)

## Change made (one concrete step, own lane, no dependency on the WinRM wall)
- `ui/app.css` `.msg`: `max-width:78%` -> `max-width:min(78%,75ch)`.
  - Why: long agent/human prose in message bubbles wrapped at up to 78% of column width,
    which on a 1440px viewport is far beyond a comfortable reading measure. Capping the
    bubble at 75ch enforces goal-5's "line-length <75ch" acceptance as a real readability fix
    (not string-gaming the check). `min()` keeps 78% on narrow/mobile viewports where 78% < 75ch.
  - File is unpinned (ui/app.css is NOT in PIN_FILES) -> edit persists, no re-pin needed.

## Remaining FAILs (next-cycle carry-forward, Designer lane — NOT the WinRM blocker)
- FAIL 2: off-scale `--fs-*` tokens orphaned ['11','13','16'] (goal 5) - decide intentional small sizes vs. fold into scale.
- FAIL 3: 4 off-scale gap values (gap:6px x3, gap:18px) (goal 2/spacing scale).
- FAIL 4: 16 ad-hoc `:hover` rules in app.css; goal 1 requires them consolidated in ui/interactions.css.

## Note on the "1 open" auto-loop artifact
Ledger shows designer **10/10 reached, open=0** (stale dashboard count). This pass is regression-maintenance
on the already-closed design-QA lane (goal 10), producing a new measurement + one fix.
