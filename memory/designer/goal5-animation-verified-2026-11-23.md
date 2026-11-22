Goal 5 Animation/Motion System - verified 2026-11-23.

All 5 keyframe animations present in ui/animations.css:
- panel-enter (150ms ease-out, transform+opacity)
- li-enter (150ms staggered 30ms/item, transform+opacity)
- gauge-fill (350ms ease-in-out, width)
- ring-fill (350ms ease-in-out, stroke-dashoffset)
- notif-slide-in (200ms ease-out, transform+opacity)

Max duration = 350ms < 400ms criterion. PASS.
prefers-reduced-motion media query disables all + snaps gauges to final value. PASS.
Layout-shift-free: transform/opacity/stroke-dashoffset only; gauge width anim contained in overflow-hidden bar. PASS.

Consumers (live): fleet composite .fh-bar-fill, UI.gauge() ring, panel enter on open, toast/notif slide-in.

Fix this pass: --anim-duration-slow reduced 600ms -> 350ms to meet <400ms criterion.
