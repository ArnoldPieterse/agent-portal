# Goal #6 Progress - Loading Skeleton Screens (2026-11-18)

## What was done
Implemented skeleton loading screens for all 4 panels:

### CSS (ui/app.css)
- `@keyframes shimmer` - 1.4s ease-in-out infinite background-position sweep
- `.skel` base class with ::after pseudo-element for shimmer gradient
- `.skel-row`, `.skel-dot`, `.skel-line`, `.skel-bar-track` - atomic skeleton primitives
- `.skel-stack` - vertical flex container matching panel padding
- `.skel-host-row` - matches .frow-h layout (dot + name + sub-lines)
- `.skel-ops-grid` - 2-col grid for ops tiles
- `.skel-tile` - matches disk/uptime tile dimensions

### JS (ui/core.js)
- `skelFleet()` - returns HTML: 3 host rows (dot + 2 lines each)
- `skelGoals()` - returns HTML: 4 goal bar rows (label + track + value)
- `skelOps()` - returns HTML: 2-col tile grid + log area block
- `skelFiles()` - returns HTML: 3 generic row skeletons
- `showSkel(id, html)` / `clearSkel(id)` - helper functions

### Wiring
| Panel | Trigger | Skeleton shown | Cleared by |
|-------|---------|---------------|------------|
| fleetPanel | First fleetUpdate (no timer yet) | skelFleet()+skelGoals() in #fleetBody | innerHTML replace on data arrival |
| opsPanel | Every opsLoad() call | skelOps() in #opsBody | innerHTML/textContent replace |
| actPanel | First open of panel | 3-row skeleton in #actBody | actRender() replaces content |
| filesPanel | Every filesLoad() call | 3-row skeleton in #filesList | innerHTML replace on data |

## Layout-shift prevention
- Skeletons use identical CSS custom properties for padding/margins as real content
- .skel-host-row mirrors .frow-h flex structure (dot + column)
- Goal bar skeletons reuse .gbar-row class from real bars
- No fixed pixel heights - all via tokens (--vh-panel, --vh-row, --sp-*)

## Acceptance criteria status
- [x] Skeletons render during API delay (shown before fetch resolves)
- [x] Match each panel's layout shape (host rows, goal bars, tiles, file list)
- [x] Shimmer animation (1.4s infinite)
- [ ] No layout shift when real content loads (needs visual verification in browser)
- [ ] Simulated 2s delay test (code path confirmed; needs live portal test)

## Files modified
- ui/app.css (+15 lines skeleton CSS)
- ui/core.js (+7 helper functions, wired into fleetUpdate/opsLoad/actBtn)
- ui/uploads.js (replaced "loading…" text with skeleton HTML in filesLoad)
