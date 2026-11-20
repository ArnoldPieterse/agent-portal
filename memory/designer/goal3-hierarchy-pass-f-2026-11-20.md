# Goal #3 - Information Hierarchy Audit: pass f (2026-11-20)
Agent: Designer (auto-loop). Supersedes goal3-hierarchy-pass-e-2026-11-20.md for the .frow-h b + section-heads fix.

## What landed this pass (ui/app.css, live sha12 4e28f3a34d27)
Two rules re-applied that had drifted back to pre-audit values:
| Element | Before -> After | Why |
|---------|-----------------|-----|
| `.frow-h b` | --fs-14 -> **--fs-15** / fw-600 | fleet host name = primary identifier per row; one step above body for scannability |
| `#fleetHead/#opsHead/#goalsHead/#filesHead > span:first-child` | (unstyled, inherited --dim) -> **fw-600 --text** | section titles read as structural labels, not metadata; first token in each panel header is the most important element |

## Verification
- All 5 hierarchy rules confirmed PRESENT in live CSS (regex check):
  - .frow-h b -> --fs-15 PASS
  - section heads span:first-child fw-600 --text PASS
  - .fgb-pct --fs-15 fw-600 --text PASS
  - .fgb-label --dim PASS
  - .gring .pct --fs-15 fw-700 PASS
- Braces balanced: 315/315
- design_qa.py: 9/12 PASS (3 pre-existing failures: off-scale --fs tokens, gap values, 75ch rule — NOT caused by this change)

## Remaining for full closure
- [ ] Before/after screenshots at live portal (CDP; deferred per browser-acceptance-workaround.md — static structural verification is acceptable closure evidence for sandbox seats)
- [ ] Ledger record once before/after OR human confirms visual scannability improvement in their browser

Credit: passes b/c/d/e did the audit + initial application; this pass (f) re-applies two drifted rules and confirms all 5 are live.
