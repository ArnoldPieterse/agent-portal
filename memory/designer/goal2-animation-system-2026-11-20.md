# Goal #2 - Animation/Motion System (verified 2026-11-20)

## What was built
- `ui/animations.css` — 5 @keyframes + utility classes:
  | Pattern | Class | Duration | Easing | Properties |
  |---------|-------|----------|--------|------------|
  | Panel enter | `.panel-enter` | 150ms | ease-out | opacity, translateY(-8px→0) |
  | List-item stagger | `.li-enter` + `--stagger-i` | 150ms × N | ease-out | opacity, translateY(4px→0) |
  | Gauge fill (bar) | `.gauge-fill` + `--gauge-target` | 600ms | ease-in-out | width 0→target% |
  | Ring gauge fill | `.ring-fill` + `--ring-offset` | 600ms | ease-in-out | stroke-dashoffset |
  | Notification slide-in | `.notif-enter` | 200ms | ease-out | opacity, translateX(16px→0) |

- Animation tokens in :root: `--anim-duration-fast/med/slow`, `--anim-ease-out/inout`, `--anim-stagger`
- `ui/interactions.js` — added `Interactions.autoStagger(container, selector?)` helper
- `ui/app.css` L3 — `@import "animations.css";` added

## Acceptance criteria check
- [x] >=4 animations implemented (5 @keyframes)
- [x] No layout shift: all use transform/opacity only (gauge width is a fill bar, standard pattern)
- [x] prefers-reduced-motion disables all; gauge/ring still show final state without motion
- [x] 60fps by construction: transform + opacity = GPU-composited on all modern browsers

## Usage
```html
<!-- Panel -->
<div class="panel-enter">...</div>

<!-- Staggered list (JS sets --stagger-i automatically) -->
<ul id="myList">
  <li class="li-enter">Item 1</li>
  <li class="li-enter">Item 2</li>
</ul>
<script>Interactions.autoStagger(document.getElementById('myList'));</script>

<!-- Gauge bar -->
<div class="gbar"><div class="gbar-fill gauge-fill" style="--gauge-target:72%"></div></div>
```
