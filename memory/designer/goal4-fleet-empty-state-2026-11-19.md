# Goal #4 (Empty State Design) - fleet panel wired + stale-claim correction
Date: 2026-11-19 (Designer, auto-loop pass)
Status: PROGRESS (code complete for all 4 panels; live-render verification still pending the CDP wall)

## What was wrong
A hot-note flagged goal #4 as having a STALE "closed" claim because `grep emptyState ui/core.js` returned
0 hits. That grep was MIS-SCOPED. Verified reality:

- `UI.emptyState()` is DEFINED in **ui/icons.js:143** and attached to the namespace at **icons.js:179**
  (`root.UI.emptyState = emptyState`) / icons.js:181 (fallback).
- **ui/icons.js is loaded** by index.html:159 (`<script src="ui/icons.js"></script>`), placed before
  core.js so `UI.emptyState` is available to every panel renderer.
- So the component existed and was already used by 3 of the 4 panels. The genuine gap was FLEET only.

## Panel-by-panel caller inventory (verified via findstr, all guarded by `window.UI&&UI.emptyState`)
| Panel   | File        | Line | icon    | CTA            |
|---------|-------------|------|---------|----------------|
| Activity| ui/core.js  | 306  | clock   | (none)         |
| Fleet   | ui/core.js  | 382  | agent   | Refresh now -> fleetUpdate   <- ADDED THIS PASS
| Uploads | ui/uploads.js| 334 | upload  | + Upload       |
| Goals   | ui/uploads.js| 362 | goal    | Open TODO.md   |

## The fix (ui/core.js, fleetUpdate())
Before: `$("fleetBody").innerHTML=html||'<div class="hint">no hosts</div>';`  (bare text hint, off-design)
After: when no hosts report, render the proper component:
```
const fb=$("fleetBody");
if(html){ fb.innerHTML=html; }
else { fb.textContent="";
  if(window.UI&&UI.emptyState){ fb.appendChild(UI.emptyState({icon:'agent',title:'No hosts reporting',
    message:'Fleet health checks run every 15s. Hosts appear here as soon as they report to /api/fleet.',
    ctaLabel:'Refresh now',onCta:fleetUpdate})); }
  else { fb.innerHTML='<div class="hint">no hosts</div>'; } }   // defensive fallback
```
- CSS `.empty-state*` already present in ui/app.css:276-280 (tokens). No CSS change needed.
- `onCta:fleetUpdate` is valid - fleetUpdate is the enclosing function (core.js:366), in scope.
- Syntax sanity: whole-file paren balance 0, brace balance 0. (Bracket delta -1 is pre-existing
  string content; this edit added no `[`/`]`.)

## Persistence / pin note
ui/core.js is NOT an entry in memory_mirror.py PIN_FILES (only index.html is pin-guarded). The ui/*.js
modules are served via GET /ui/* but are not clobber-protected by pin_guard, so this edit needs NO index.html
pin advancement. (If a future remote-sync overwrites it, recover per mirror-revert-recovery-2026-11-18.md.)

## Remaining for FULL acceptance (NOT met - same wall as goals #2/#3)
Live render: all 4 empty states actually painting when /api/* returns empty arrays + CTAs clickable.
Needs a browser. From THIS seat the portal is not listening on :8099 (netstat empty) and the python
sandbox blocks localhost egress - same repeated CDP wall documented in memory/ops/blockers.md
(2026-11-17 entry + 2026-11-18 msedge resolution). Not re-probed this pass per auto-loop rule.
Static acceptance (all 4 callers + definition present & loaded) = PASS, recorded here.
