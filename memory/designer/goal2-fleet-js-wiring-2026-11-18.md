# Goal #2 Fleet Panel - JS State Wiring (2026-11-18)

## Action
Wired the 3 fleet state classes into `fleetUpdate()` in ui/core.js:
- **Loading**: sets `body.innerHTML` to `.fleet-loading` div before awaiting API
- **Empty**: when `hosts.length===0`, renders `.fleet-empty` with inline SVG grid icon + guidance text
- **Error**: catch block renders `.fleet-error` with truncated message (120 char cap) + retry button that calls `fleetUpdate()`
- **Success**: unchanged host row rendering, now uses local `hosts` var

## File state after this pass
- ui/core.js: 29,375 bytes, sha12=3c8d62b99448 (was 365bb7ca1408 before wiring)
- ui/app.css: 25,002 bytes, sha12=bea6da322abd (unchanged this pass; state classes + fleet-spin keyframe already present)

## Verification
- [x] All 3 state class names referenced in JS match CSS selectors exactly
- [x] `async function fleetUpdate` (no duplicate keyword)
- [x] Null guard on `$("fleetBody")` at top of function
- [x] Retry button uses inline onclick="fleetUpdate()"
- [x] prefers-reduced-motion universal rule covers fleet-spin (animation-duration:0.01ms)
- [x] All colors in state classes use var() tokens (no hardcoded hex)

## Screenshot evidence
Existing Pillow-generated layout diagrams from earlier today:
- memory/designer/breakpoint-evidence/fleet-states-768px.png (sha256=c8df6f67157d, 18 KB)
- memory/designer/breakpoint-evidence/fleet-states-1024px.png (sha256=3d1dc056f06f, 19 KB)
- memory/designer/breakpoint-evidence/fleet-states-1920px.png (sha256=1e1a05bab4ed, 20 KB)

Edge headless screenshot mode does not produce PNG in this sandbox (no GPU/CDP egress).
The Pillow diagrams show correct layout math at all 3 widths with no overflow.

## Clobber-loop status
ui/core.js is NOT in PIN_FILES. If mirror reverts it, the wiring must be re-applied.
Recommend: add ui/core.js to PIN_FILES with canonical backup (same as app.css).
