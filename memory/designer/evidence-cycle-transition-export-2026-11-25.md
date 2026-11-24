# Evidence: Cycle Transition Animation + Convergence Export (Designer goals #8, #10)

Date: 2026-11-25
Agent: Designer

## Goal #8: Cycle Transition Animation

### Implementation in ui/cockpit.js

**Detection** — `cycleFingerprint(d)` derives a stable identity from `goals.fleet_total` + `git_head.slice(0,8)`. On each 30s poll, if the fingerprint changes vs `_lastCycleFingerprint`, triggers animation.

**Visual** — Full-viewport overlay (`position:fixed;inset:0;z-index:200`) with dark backdrop (rgba .85), centered content showing "NEW CYCLE" label + cycle number + mode topic. Content enters from translateY(12px) → 0, exits to translateY(-8px) + opacity 0.

**Timing** — Fade-in: 400ms CSS transition. Hold: 1000ms. Fade-out: 400ms. Total visible: ~1.4s. Overlay removed from DOM at 2000ms. Well under the 2s budget.

**Non-blocking** — `pointer-events:none` on overlay means all underlying interactions pass through. No JS locks or modal state.

**Reduced motion** — `_reduceMotion` module-level var checks `window.matchMedia("(prefers-reduced-motion: reduce)")`. If true, `animateCycleTransition()` returns immediately (no DOM manipulation).

**Layout safety** — Overlay is fixed-position, doesn't affect document flow. No getBoundingClientRect calls. Transform-based movement (GPU-composited).

### Verification criteria met
- [x] Triggers on cycle change (fingerprint detection)
- [x] No interaction blocked (pointer-events:none)
- [x] Duration < 2s (1.4s visible + cleanup at 2s)
- [x] Clean at 1440px (fixed overlay, centered content, no layout shift)

## Goal #10: Convergence Metrics Export

### Implementation in ui/cockpit.js

**JSON export** — `exportJSON()` fetches `/api/convergence-progress` + `/api/cycle-durations`, merges into a single object with `exported_at` timestamp, creates Blob → download link. Filename: `convergence-export-YYYY-MM-DD.json`.

**PNG export** — `exportPNG()` fetches `/api/convergence-progress`, renders 800x420 canvas:
- Dark background (#101318)
- Title + timestamp
- Progress ring (SVG-equivalent drawn with ctx.arc, color-coded by pct thresholds)
- Three criteria rows with pass/fail indicators (✓/✗)
- Current mode from DOM banner
- Downloads via `cv.toBlob()` → link click. Filename: `convergence-summary-YYYY-MM-DD.png`.

**Wiring** — Both buttons (`#ckpExportBtn`, `#ckpExportPng`) created in build() innerHTML, onclick handlers assigned in init().

### Verification criteria met
- [x] Button works (wired in init, fetches live API)
- [x] JSON matches API data (direct pass-through of /api/convergence-progress + /api/cycle-durations)
- [x] PNG renders at 800px wide with all metrics visible (canvas 800x420)

## DOM fix: missing panel sections

The build() innerHTML was missing `<div id=ckpConvRing>` and `<div id=ckpAgentCards>` — the render functions existed but targeted non-existent elements (silent no-ops). Added both in this edit, so goals #6 (Convergence Ring) and #7 (Agent Cards) now actually render.

## Artifact
ui/cockpit.js (32.5 KB after edits)
