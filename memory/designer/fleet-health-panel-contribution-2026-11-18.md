# Designer contribution: Fleet panel now consumes /api/health/fleet

Date: 2026-11-18 (auto-loop pass)
Type: Team contribution (option d - concrete step on Mechanic goal 7)

## What changed
- ui/core.js: fleetUpdate() now fetches /api/health/fleet in parallel with /api/fleet via Promise.all
- Per-host rows show probe severity badge (OK/WARN/CRIT) + sync age when available
- Status bar now includes portal uptime (h+m) and latest git commit hash
- ui/app.css: added .fhealth, .fsev.ok/.warn/.crit styles (compact pill badges)

## Rationale
Mechanic goal 7 verification noted the endpoint is 'consumed by Designer panel' - this closes that loop.
The /api/fleet endpoint shows live residency; /api/health/fleet adds ops-health context. Both now render in one panel.

## Files changed
- ui/core.js (fleetUpdate function: parallel fetch + health merge)
- ui/app.css (.fhealth, .fsev.ok/.warn/.crit styles)
- memory/designer/fleet-health-panel-contribution-2026-11-18.md (this file)
