# Goal #2 Fleet Panel States - Re-apply 3 (mirror-revert again, 2026-11-18)

## Action
Re-applied fleet loading/error/empty states to ui/app.css + ui/core.js after mirror-revert.
Also re-added prefers-reduced-motion block (was also reverted).

## Current file state
- app.css: 23,931 bytes, sha12=4c57c147fafd
- core.js: 29,247 bytes, sha12=2d13e39b91c6
- uploads.js: unchanged (total bundle 56.7 KB minified, well under 80KB goal #3 budget)

## CSS additions (after #fleetBtn rules, before #opsPanel)
- .fleet-loading - flex row, animated spinner via ::before + fspin keyframe
- .fleet-error - left-border banner, color-mix tint background, var(--err) color
- .fleet-empty - centered column with SVG icon + guidance text
- @keyframes fspin - 360deg rotation
- @media(max-width:1024px) - reduced max-height for fleet panel + topo width:100%
- @media(prefers-reduced-motion:reduce) - disables fspin/fdot/dot animations

## JS changes (fleetUpdate function)
- Guards null body element
- Empty hosts array → .fleet-empty with SVG grid icon + "No hosts reporting" message
- API error → .fleet-error banner with truncated error (120 chars max)
- Success path unchanged (host rows render as before)
- fleetStat updated in both success and error paths

## Static verification
- [x] All 4 state classes present in CSS (grep confirmed)
- [x] All use var() tokens - zero hardcoded colors
- [x] fspin covered by prefers-reduced-motion block
- [x] Media queries at 1024/768/375 present
- [x] Bundle total 56.7 KB < 80KB budget
- [x] No overflow risk: .fleet-empty uses flex-column centering; .fleet-error has no fixed width; .fleet-loading is single-row flex

## Remaining for full acceptance (requires browser)
- [ ] Screenshot evidence at 3 resolutions (msedge --screenshot times out in sandbox -
      breakpoint_gate.py logic test also times out due to CDP launch failure)
- [ ] Dark mode visual check of new states (all use var() tokens so should be theme-correct)

## Note
This is the THIRD re-application of these same changes. The mirror cycle keeps reverting
ui/app.css and ui/core.js. If this continues, the pin mechanism needs to cover ui/ files
to prevent the clobber loop.
