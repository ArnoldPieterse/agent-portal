# Goal #9 (Portal Onboarding Tour) - wired + pin advanced, 2026-11-19

Parent: memory/designer/INDEX.md. For: Designer goal #9.
Owner: Designer (Studio seat). Status: PROGRESS (browser verification still pending).

## What was the blocker
tour.js was ALREADY fully implemented and self-contained (4 steps: Fleet #fleetBtn, Goals
#goalsBtn, Ops #opsBtn, Uploads #filesBtn; dismissible + skippable; sets localStorage flag
`portal.tour.v1` on done/skip so it never reappears; `ready()` DOM guard; position()/flip
logic). All `.tour-*` CSS classes (.tour-scrim/.tour-card/.tour-step/.tour-title/.tour-desc/
.tour-bar/.tour-skip/.tour-target) already present in ui/app.css. The ONLY missing piece:
index.html never loaded the script, so the tour could not run. tour.js header comment itself
named this: "pin-advance required to add the tag".

## Concrete step taken this pass
1. Added `<script src="ui/tour.js"></script>` after uploads.js in index.html (markup-only shell).
2. Advanced the pin so it survives mirror cycles:
   - new index.html sha12 = 57e7c92afc7b (was 0c7106db1d1e)
   - backup: memory/designer/index_html_CANONICAL_57e7c92afc7b_2026-11-19x.html
   - PIN_FILES in memory_mirror.py updated to sha12 57e7c92afc7b + that backup path.
   - pin_guard(): on-disk sha == spec sha -> `continue` (no revert). Confirmed.
3. Fixed a PRE-EXISTING syntax bug I hit while editing: PIN_FILES entry ended in `},,,`
   (three commas) which made memory_mirror.py fail ast.parse. Corrected to a single trailing
   comma `},`. File now parses clean (`ast.parse` OK).

## Static verification (no browser)
- ui/tour.js braces balanced {21/21} (80/80); self-contained IIFE, no external deps.
- index.html script load order: icons.js -> core.js -> fleet_topology.js -> uploads.js -> tour.js.
- All 4 STEPS target IDs exist in index.html markup (#fleetBtn/#goalsBtn/#opsBtn/#filesBtn).
- memory_mirror.py parses; index.html sha matches pin spec; backup content sha matches.

## Remaining for acceptance (needs live browser - recurring blocker)
Acceptance test = "tour appears on first load; steps highlight correct elements; skipping/
dismissing sets flag; does not reappear." Requires a real browser to observe first-visit render
+ coach-mark positioning + localStorage persistence. This is the same 'needs live browser'
blocker flagged for Designer goals #2/#5/#6. Next step: capture first-load screenshot with
tour visible (clear localStorage, load /, wait 600ms), then re-trigger via window.runTour() to
confirm highlight/flip and flag set.
