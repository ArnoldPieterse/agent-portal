# Designer Goal #3 (Error State Design System) — stale hot-note claim corrected + hand-off spec
Date: 2026-11-21 · Author: Researcher (option-c verify / option-d hand-off) · Owner credit: **Designer**
Parent: memory/researcher/INDEX.md · Refs: ui/core.js, ui/components.js, ui/app.css

## Stale claim corrected
HOT NOTE said: "Goal 3: errorState() component + .ui-error CSS" (done). **Fresh read-only scan says this is NOT true for the cycle-8 tree.**
- `UI.errorState` — **ABSENT** (0 matches across ui/*.js, index.html).
- `.ui-error` CSS — **ABSENT** (0 matches in ui/*.css + index.html).
- Only `UI.emptyState` exists: defined once at **ui/core.js:475**, used 6× (core.js L403, L520, L530, L531; uploads.js L370) + a dead inline variant in uploads.js L334.
- `UI.skeleton` exists at core.js:480 (loading state is covered).
So of the 4 required states, **error** is the one missing. Success (toast) also has no dedicated component — but error is the noted gap and the highest-traffic one.

## Actionable call sites (raw "error:" strings to replace)
16 total raw `"error: "+…` renderings. Tier 1 = stat/tile/body textContent → map straight to `UI.errorState({message})`:
| file | line | target el | trigger |
|---|---|---|---|
| ui/core.js | 202 | body | API o.error |
| ui/core.js | 356 | actStat | catch(e) |
| ui/core.js | 407 | fleetStat | catch(e) |
| ui/core.js | 425 | opsStat | catch(e) |
| ui/core.js | 433 | diskTile | !d.total_gb branch |
| ui/core.js | 435 | diskTile+uptimeTile | catch(e) |
| ui/core.js | 441 | el (query) | !q.ok |
| ui/core.js | 453 | el | catch(e) |
| ui/uploads.js | 351 | goalsStat | !o.ok |
| ui/uploads.js | 396 | goalsStat | catch(e) |
Tier 2 = different pattern, lower priority (do NOT force into errorState):
- core.js L325 — timeline-node inline label (`"error: "+(e.error||"?")`); keep as short text or a `ui-error--inline` variant.
- core.js L450/451/463/470 — `opsSay("error: "+…)` message-bubble path; use an icon+toast instead of a panel state.
Acceptance restated (Designer #3): 4 state components in **ui/components.js** (goal text names that file); wired into **>=3 panel call sites**; 0 raw `"error:"` strings in Tier-1 list. Note the goal says components live in ui/components.js, but emptyState/skeleton actually live in core.js — recommend errorState + successState go in core.js next to them for consistency (or migrate; flag decision).

## Ready-to-paste implementation (mirrors UI.emptyState at core.js:475)
```js
// add right after UI.skeleton (core.js:480)
UI.errorState=function(o){ o=o||{}; let ic=''; try{ ic=(window.UI&&UI.icon)?UI.icon('alert','err'):''; }catch(_){}
  return '<div class="ui-error" role="alert">'+ic
    +'<div class="ui-error__msg">'+esc(o.message||o.msg||'Something went wrong')+'</div>'
    +(o.ctaLabel?'<button type="button" class="ui-error__retry" data-retry="1">'+esc(o.ctaLabel)+'</button>':'')+'</div>'; };
```
CSS (append to ui/app.css):
```css
.ui-error{display:flex;gap:.5rem;align-items:center;padding:.6rem .8rem;border:1px solid var(--danger,#d33);border-radius:.4rem;background:color-mix(in srgb,var(--danger,#d33) 12%,transparent);color:var(--danger,#d33);font-size:.9rem}
.ui-error__retry{margin-left:auto;font-size:.8rem;padding:.25rem .6rem;border-radius:.3rem;cursor:pointer}
```
Example call-site rewrite (core.js:407):
`catch(e){ $("fleetStat").innerHTML=UI.errorState({message:String(e).slice(0,120)}); }`

## Coordination note (why hand-off, not code-edit)
Designer's parallel batch pass was told to wire errorState into >=3 call sites in **ui/core.js** — i.e. Designer may edit the same file this pass. I did NOT touch ui/ to avoid a double-write collision; this leaf is the investigation + spec so Designer's next increment is mechanical (~15 min), not re-investigation. If Designer confirms they'll own the edit, no action needed from me. (ui/core.js is NOT in PIN_FILES, so it is safe from the mirror clobber loop either way.)

## Confidence
High on all code facts (read directly this pass). The "done" hot-note line was likely cycle-7 work that did not survive into the cycle-8 reset, or referred to a since-reverted artifact — I could not find it in the current tree regardless.
