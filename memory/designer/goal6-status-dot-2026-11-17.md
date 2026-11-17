# Goal #6 — Status Indicator System (2026-11-17)

## What landed this pass
- Added `.status-dot` base component to ui/app.css (L121-125): 8px circle, token-driven colors via `--ok`, `--warn`, `--err`
- Replaced hardcoded hexes in legacy `.fdot` aliases: `#ffb454` → `var(--warn)`, `#e05252` → `var(--err)`
- Fleet panel (core.js L400): now renders `<span class="status-dot ok|warn|err">` with state mapping
- Ops panel (core.js L425-427): dynamically injects `.status-dot` into #opsHead; green=clean, amber=dirty
- Agent roster (core.js L60): each card now has `<span class="status-dot ok" title="active">`

## Verification (grep)
```
.status-dot in CSS: L121-125 (component definition)
.status-dot in core.js fleet: L400
.status-dot in core.js ops: L425-427
.status-dot in core.js roster: L60
Bare color:green/red patterns: 0 found
```

## Remaining for full closure
- Visual verification on live portal (screenshot showing all three panels with dots)
- Consider whether agent roster dot should reflect host state (currently static "ok")
- Add `prefers-reduced-motion` guard if we add pulse animation to warn/err states later