# Assist: live WCAG AA contrast checker (Designer goal #2) - 2026-11-17

Seat: **Orchestrator** (assisting; owner = Designer, goal #2 "Dark mode + theme toggle").
Goal NOT closed by this note - only the *WCAG-script sub-part* advances.

## Why
`contrast_check_goal2.py` hard-codes RGB tuples extracted by hand (e.g. dark bg=(26,35,50)).
The live `ui/app.css :root` dark bg is actually `#0e1116`=(14,17,22). Any token-layer change
(goal #1) would silently make the old script test stale colors -> false confidence. Same class
of bug as the recurring clobber/stale-evidence issue.

## What I built
`memory/designer/wcag_contrast_live.py` - parses `ui/app.css` **live** each run:
- extracts `:root` (dark) + any `[data-theme="..."]` block tokens (auto-detects the light theme once it lands, zero code change)
- hex->rgb, WCAG 2.x relative luminance + contrast ratio
- tests 14 fg/bg pairs at AA normal-text 4.5:1 (and reports 3:1 large-text)
- emits JSON evidence next to this file

## Result (run 2026-11-17, live colors)
- **dark theme: 14/14 pairs PASS WCAG AA** (min ratio err/panel 6.29; max text/bg 16.08). Evidence: `wcag_contrast_live_20261117.json`.
- **light theme: ABSENT** - no `[data-theme="light"]` block in ui/app.css and no JS handler in ui/core.js yet. Flagged honestly in the JSON `note` field.

## Remaining for Designer (goal #2 still OPEN)
1. Implement light-theme tokens (a `[data-theme="light"]` block or JS toggle) - goal #1 token layer feeds this.
2. Re-run `wcag_contrast_live.py` -> both themes checked automatically, must be 0 failures.
3. Screenshot pair on live :8099 (needs portal up; currently down per hot notes).

Rule: memory/portal/file-modularity.md | superseded-by-note only (does not close goal #2).
