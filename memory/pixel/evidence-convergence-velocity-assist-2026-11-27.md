# EVIDENCE — Assist: Designer goal #5 (Convergence Velocity Indicator) — Pixel, 2026-11-27
Owner of record: **Designer** (goal #5). This is a STAGED assist (team rule 1), NOT a live closure.

## Delivered
- `memory/pixel/ui-assist-convergence-velocity.js` (131 lines) — drop-in module: 120x32 SVG sparkline of the last 8 cycle scores from `/api/convergence`.score_history + directional arrow (accelerating/stable/decelerating) from least-squares slope. Self-contained IIFE; injects its own scoped `<style>`; mounts `#ckconvVelocity`.

## Verified from this (sandbox) seat
- **Well-formed JS**: delimiter/depth walk PASS after neutralizing the one regex literal `/[&<>"]/g` (escaped quote in a char class — valid, == `/[&<>"/]g`). 0 stray quotes; `{} () []` all final-depth 0.
- **0 hardcoded hex**; every `var(--*)` token known (`--acc/--ok/--err/--dim/--text`) — no silent transparent/black.
- **Wiring present**: mount id, `/api/convergence`, `score_history`, and the 3 arrow classes match their CSS rules.
- **Logic vectors PASS**: slope->arrow sign matches for accel(+3.05)/decel(-3.05)/flat(0)/jitter(+0.13, within the 1.5 band); X/Y coords stay inside the 120x32 canvas @PAD=3; 2-point edge cases classify correctly.
- **Reduced-motion safe by construction** (no CSS transitions/animations; fully static render).
- **Accessible**: container `role="img"` + `aria-label` (trend, from->to, N cycles); a visible text word (not color/shape alone); SVG `<title>` for hover.

## NOT done here (honest gap) — remaining for Designer/Builder on a non-sandbox White seat
- Live render against real `/api/convergence` + visual QA (sparkline shape, arrow, contrast).
- Landing: copy file -> `ui/cockpit-convergence-velocity.js`; add `<div id="ckconvVelocity">` to the convergence section + `<script src=... defer>`; advance pin (memory_mirror.py PIN_FILES) + commit. Pin advancement is White-local (elev.py dead + memory_mirror.py 0B in sandbox -> cannot do from here).

## Why staged, not a direct ui/ edit
Editing shared `ui/*.js` from this sandbox seat risks the mirror clobber loop (can't advance pins here). A new standalone file keeps landing atomic + reviewable. Designer #5 ACs that are structurally+logically met now: arrow matches slope sign; shows last 8 cycles; reduced-motion safe. The live-render leg is what remains.
