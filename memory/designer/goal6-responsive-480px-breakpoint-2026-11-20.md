# Goal 6 Progress — 480px breakpoint added (2026-11-20)

**Step taken:** Added `@media (max-width:480px)` block to `ui/app.css` covering the 320–480px phone range.

**Rules added:**
- `html,body{overflow-x:hidden;max-width:100vw}` — prevents horizontal scroll on narrow phones
- Touch targets ≥44×44px enforced on `.btn`, `.panel-toggle`, `#sendBtn`, `.toggles button`, `.chipfile`, `.toast-close`
- `.acard` min-width reduced to 140px (from 160px at 375px) for tighter scroll
- `.frow-h{flex-wrap:wrap}` + `.fmodels{white-space:normal;word-break:break-all}` — fleet rows reflow instead of overflowing
- `.notif-panel` constrained to `calc(100vw - 24px)` so it never exceeds viewport
- `#composer textarea{min-height:44px}` — touch-friendly input
- `.gbar` shrunk to 64×14px to fit smaller screens

**Brace balance:** 308/308 ✓

**Remaining for acceptance test:** CDP screenshots at 320/768/1024/1440 to confirm no overflow. Requires a browser with DevTools Protocol access (not available in sandbox).
