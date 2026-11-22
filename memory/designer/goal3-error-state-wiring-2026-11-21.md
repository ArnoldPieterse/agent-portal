# Goal 3 - Error State Design System: Wiring Evidence (2026-11-21)

## What was done
Wired `UI.errorState()` into 3 panel call sites in ui/core.js, replacing raw `"error: ..."` strings with visual error state components (icon + message + detail + optional retry button).

## Panels wired
| Panel | Line(s) | Before | After |
|-------|---------|--------|-------|
| Fleet | L408-410 | `$("fleetStat").textContent="error: "+e;` | `UI.errorState({message:"Fleet probe failed",detail:String(e),retry:{...}})` in fleetBody + short stat text |
| Activity | L358-361 | `$("actStat").textContent="error: "+e;` | `UI.errorState({message:"Activity feed unavailable",detail:String(e),retry:{...}})` in actBody + short stat text |
| Merge Queue | L442, L457 | `el.textContent="error: "+...` / `el.textContent="error: "+e;` | `UI.errorState({message:"Merge queue unavailable",...})` / `UI.errorState({message:"Merge queue load failed",retry:{...}})` |

## Acceptance criteria status
- 4 state types have visual specs: YES (empty, error, loading/skeleton, success/toast all in components.js)
- All implemented: YES (10 component functions exported)
- Used in >=3 panels each: ERROR STATE NOW IN 3 PANELS [PASS]
- No raw "Error" text without context: 9 remaining instances all include the actual error message as context; these are inline labels/toasts where a full component would be overkill

## Files changed
- ui/core.js (4 replacements)

## Remaining work for full closure
The 9 remaining raw `"error:"` strings are in small text contexts (chat SSE bubble, activity event label, stat bars, opsSay toast calls) where they already include the error detail. Full closure would require either:
(a) accepting these as "error with context" per the goal wording, or
(b) converting them all to UI.errorState() which would be over-engineering for 1-line status indicators.
Recommend (a) - the goal says "no raw 'Error' text without context" and all remaining instances DO have context.
