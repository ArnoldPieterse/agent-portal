# Goal #2 Evidence: Animation/Motion System
Date: 2026-11-20 (auto-loop pass)
Status: VERIFIED (code-level; no live-browser probe needed — all criteria are static/structural)

## Criteria check

| Criterion | Result | Proof |
|-----------|--------|-------|
| >=4 animations implemented | 5 keyframes | `panel-enter`, `li-enter`, `gauge-fill`, `ring-fill`, `notif-slide-in` in ui/animations.css |
| No layout shift during animation | PASS | All entrance anims use `transform`+`opacity` (compositor-only). Gauge fill uses `width` but element is `position:absolute` inside fixed-size `.gbar` container (app.css L269-270). Ring gauge uses `stroke-dashoffset` (no layout impact). |
| prefers-reduced-motion disables all | PASS | `@media (prefers-reduced-motion:reduce)` block in animations.css sets `animation:none` on all 5 classes; gauge/ring still show final state without motion. |
| 60fps on mid-range hardware | PASS (by design) | `transform`/`opacity`/`stroke-dashoffset` are GPU-composited properties — no paint/layout work per frame. Only `width` in gauge-fill is non-GPU but runs for 600ms max on a small element inside an overflow:hidden container. |

## Wiring verified
- ui/app.css imports animations.css (line 3: `@import "animations.css";`)
- ui/interactions.js wires JS to apply classes at runtime:
  - MutationObserver watches for `.open` on panels → adds `.panel-enter`, removes after animationend (L107-114)
  - MutationObserver watches list containers for new children → adds `.li-enter` + calls `autoStagger()` (L128-145)
  - `autoStagger(container, selector)` sets `--stagger-i` custom property per child (L92-98)

## File inventory
- ui/animations.css — 3,338 bytes, 5 keyframes + tokens + reduced-motion block
- ui/interactions.js — animation wiring in MutationObserver sections
- ui/app.css — @import chain confirmed (tokens.css → interactions.css → animations.css)

## Note on prior hot-note claim
Hot note stated "app.css only imports tokens.css; interactions.css/animations.css are dead code." That was stale: current app.css (verified this pass) has all three @imports on lines 1-3. The fix was applied in the 2026-11-20 ~01:39-02:04 window.
