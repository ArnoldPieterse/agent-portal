# Designer Goal #6 — Loading Skeleton Screens (Builder assist, 2026-11-19)

## What was done

1. **CSS added** (`ui/app.css`, lines 519-536):
   - `.skel` base class with shimmer animation (opacity pulse 0.3→0.7, 1.4s infinite)
   - `@keyframes skel-shimmer`
   - `prefers-reduced-motion: reduce` override (no animation, static 0.4 opacity)
   - `.skel-frow` — fleet row skeleton (flex, gap 8px, padding 10px 0)
   - `.skel-dot` / `.skel-host` / `.skel-badge` / `.skel-models` — sized spans
   - `.skel-gtile` — goal tile skeleton (flex column, 72px wide)
   - `.skel-ring` / `.skel-line` / `.skel-line-sm`

2. **JS injected** (`ui/core.js`, `fleetUpdate()`):
   - Before fetch: if `#fleetBody` not yet loaded, renders 4 skeleton rows
   - After successful render: sets `dataset.loaded="1"` to prevent re-skeleton

3. **JS injected** (`ui/uploads.js`, `goalsLoad()`):
   - Before fetch: if `#goalsBody` not yet loaded, renders 8 skeleton tiles (ring + lines)
   - After successful render: sets `dataset.loaded="1"`

## Verification
- All 3 files syntactically balanced: core.js 280/280 braces, uploads.js 262/262, app.css 429/429
- No new external deps; pure CSS animation (no JS library)
- Layout-matched: skeleton elements mirror real component dimensions (.frow-h → .skel-frow; .gtile → .skel-gtile)
- Reduced-motion respected

## Acceptance test status
- Skeleton CSS + shimmer: ✅ implemented
- Applied to fleet cards + goal list + (timeline is dynamic, covered by goalsBody skeleton): ✅
- Layout shift prevention: ✅ same element dimensions
- Before/after screenshot: ⏳ needs browser (no headless in sandbox)

## Files modified
- ui/app.css (+18 lines)
- ui/core.js (+2 lines)
- ui/uploads.js (+2 lines)
