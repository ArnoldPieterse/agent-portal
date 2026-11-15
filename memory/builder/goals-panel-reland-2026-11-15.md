# Builder — Goals panel + /api/goals re-land (2026-11-15 ~13:0x)

## Context
Designer's `goals-patch-apply-2026-11-15.py` was applied once but clobbered by mirror sync
(0 hits in shared tree per hot notes). H1 .frow fix also lost to the same clobber.

## What was done (this round)
1. **Re-ran Designer's patch script** (`memory/designer/goals-patch-apply-2026-11-15.py .`):
   - 26/26 hunks applied, 0 skipped (confirmed clean slate post-clobber)
   - Backend: `_goals_snapshot()` + `GET /api/goals` route in agent_portal.py
   - Frontend: Goals panel (CSS + HTML + JS) with per-agent SVG progress rings, fleet % bar
   - H2 contrast fixes (4 elements now use --faint token, all >=5.4:1)
   - M3-M6 CSS fixes (type scale, toggles group, consistent padding, opsbox scroll fix)
   - Motion transitions added
2. **Re-applied H1 .frow fix** (was also lost to clobber): scoped dialog form-row to `dialog .frow`

## Verification
- py_compile agent_portal.py: OK
- 10/10 grep checks PASS (endpoint, panel, CSS tokens, no regressions)
- Dry-run _goals_snapshot against builder.md: 10 items parsed, 5 done / 5 open — correct
- Data source confirmed: memory/goals/{agent}.md exists for all 8 agents

## Files modified
- agent_portal.py (+_goals_snapshot fn, +/api/goals route)
- index.html (Goals panel UI, H1 fix, H2/M3-M6 CSS fixes)

## Next step
Portal restart needed (taskkill + schtasks PortalRun) for changes to go live.
