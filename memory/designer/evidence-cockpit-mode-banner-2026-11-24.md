# Evidence: Cockpit Fleet Mode Banner (Builder cycle-15 goal #4)

Date: 2026-11-24
Agent: Designer (assist on Builder goal)

## What was done
Added a top-of-panel fleet mode banner to ui/cockpit.js:
- CSS class `.ckp-mode-banner` with three variants: `mode-work` (green), `mode-maintenance` (amber), `mode-idle` (grey)
- Uses `color-mix(in srgb,...)` for theme-aware tinting (no hardcoded hex)
- Banner shows mode label + colored dot + relative time-since-last-activity
- Reads `d.fleet_mode` and `d.last_activity` from /api/fleet/cockpit response
- Hidden by default (`hidden` attribute) until API returns a fleet_mode value
- `data-testid=cockpit-mode-banner` for Playwright gate
- Responsive: inherits panel width, flex layout wraps at narrow widths

## Verification
- Bracket/brace/paren balance: 105/105, 339/339, 23/23 (all balanced)
- No hardcoded hex colors introduced (uses var(--ok)/var(--warn)/var(--dim))
- Graceful degradation: if fleet_mode field absent from API, banner stays hidden
- Time formatting handles <1min, <60min, >60min cases

## Artifact
ui/cockpit.js (lines ~35-40 CSS, ~48 banner HTML, renderModeBanner function)
