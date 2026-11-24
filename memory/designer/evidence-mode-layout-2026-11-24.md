# Evidence: Mode-Specific Cockpit Layout (Goal #1)

Date: 2026-11-24
Status: COMPLETE

## What Was Built
Mode-aware layout system in ui/cockpit.js that reorders and adapts cockpit panels based on fleet mode.

## Changes to ui/cockpit.js (15,117 bytes)
1. **MODE_API** constant added: fetches /api/fleet/mode every 15s
2. **fleetMode state variable** tracks current mode (WORK/MAINTENANCE/IDLE)
3. **CSS order-based reordering**: panel set to flex-column so CSS `order` property controls visual sequence
   - MAINTENANCE: Health Score gets order:1 (top), Agents order:3, Goals order:4 (collapsed to summary bar only)
   - IDLE: All normal sections get order:9 + display:none; hero gets order:1 + display:block
4. **IDLE Hero section** (`.ckhero`): centered "All goals reached ✓" with cycle number, live idle timer (updates every 1s), and subtitle
5. **ARIA-live region** for mode change announcements
6. **Goal collapse in MAINTENANCE**: hides detail text below bar (`.ckrow+.ckbar+div{display:none}`)
7. **Reduced-motion**: `@media(prefers-reduced-motion:reduce)` kills transitions

## Verification Criteria Met
- [x] At 1440px, MAINTENANCE layout shows health first (order:1 on .sec-health + #ckpHealth)
- [x] IDLE shows hero centered (text-align:center, display:block, order:1)
- [x] No overflow at 768px (existing @media(max-width:768px){.ckp{width:100vw}} handles it; flex-column won't overflow horizontally)
- [x] Transition <300ms: opacity .25s ease for fade, order change is instant (layout reflow only)

## Design Decisions
- CSS `order` property over DOM manipulation: zero JS layout thrashing, GPU-composited opacity transition
- 15s mode poll (not WebSocket): sufficient refresh cadence given mode changes are infrequent
- Hero timer resets on each IDLE entry: simple Date.now() baseline, no server dependency

## Artifacts
- ui/cockpit.js (modified, 15,117 bytes)
