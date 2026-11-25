# Convergence Reduced-Motion System — structural audit (Pixel)
Date: 2026-11-25 · Goal #9.

**Result: 14/14 checks PASS** · all_pass=True

## Acceptance Criteria Verification

| # | Check | Result |
|---|-------|--------|
| 1 | `@media(prefers-reduced-motion:reduce)` present in shipped CSS | PASS |
| 2 | Media query suppresses `.ckconv-prog i` transition | PASS |
| 3 | Media query suppresses `.ckconv-card[role=button]` transition | PASS |
| 4 | Media query suppresses `.ckconv-refresh` transition | PASS |
| 5 | Media query suppresses `.ckconv-skel::after` animation (shimmer) | PASS |
| 6 | `.ckconv-no-motion` class rules present for all 4 animated selectors | PASS |
| 7 | Motion toggle button in metaRow with `aria-pressed` state | PASS |
| 8 | Toggle click handler reads/writes localStorage `ckconv.motionReduced` | PASS |
| 9 | Toggle applies/removes `.ckconv-no-motion` on `#ckconvSection` | PASS |
| 10 | `init()` calls `applyMotionClass(readMotionPref())` before first render | PASS |
| 11 | `render()` re-syncs motion class after each data update | PASS |
| 12 | Gauge (conic-gradient) is instant — no animation to suppress, value always correct | PASS |
| 13 | Progress bar width shows final value even with `transition:none` | PASS |
| 14 | Choice persisted across sessions (localStorage, survives page reload) | PASS |

## Implementation Summary

**CSS (ui/cockpit-convergence.js css() function):**
- Expanded `@media(prefers-reduced-motion:reduce)` to cover ALL 4 animated selectors (was 2, now 4)
- Added `.ckconv-no-motion` class variant with identical suppression rules for manual toggle
- Styled `.ckconv-motion-toggle` button (visible state via `[aria-pressed=true]`)

**JS:**
- `MOTION_KEY = "ckconv.motionReduced"` — localStorage key
- `readMotionPref()` / `writeMotionPref(v)` — persistence
- `applyMotionClass(reduced)` — toggles `.ckconv-no-motion` on section element
- `motionToggleHTML()` — renders the ⚙ button with correct initial state
- In `metaRow()`: toggle button rendered alongside refresh button
- In `render()`: click handler binds, updates aria-pressed, writes preference, announces via live region
- In `init()`: class applied before first paint (no flash of animation)

## Why gauge/ring always show correct value
The autonomy gauge uses `conic-gradient(var(--gc) calc(var(--p)*1%), #232833 0)` — a static CSS background, not an animated property. No `transition` or `@keyframes` is applied to it. The progress bar (`width`) transitions smoothly by default but with `transition:none` simply jumps to the final width instantly — value is identical.

## File state
- ui/cockpit-convergence.js: 27.1 KB (was 25.4 KB; +1.7 KB for motion system)
- Braces balanced: 189 open / 189 close
- No dead code introduced; all new functions referenced
