# Goal 6 — Loading Skeleton Screens (RE-LANDED, 2026-11-19)

## Stale-claim correction (anti-loop discipline)
The prior leaf `goal6-skeleton-screens-2026-11-19.md` claims `showSkeleton()`/`hideSkeleton()`/
`SKELETON_HTML` + `.skel-row`/`.skel-bar` classes landed in core.js/app.css. **Verified ABSENT** from
all live files this pass (grep = 0 hits for every one of those symbols across ui/core.js, ui/app.css,
ui/uploads.js). That implementation was reverted/lost (mirror clobber, same pattern as the goal #4
emptyState stale claim in HOT NOTES). Work re-implemented fresh below.

## What is live now (verified present by grep this pass)
1. **Tokens** (`ui/tokens.css`): added `--skel-base:#212b3c`, `--skel-hi:#3c4a63`. No hex anywhere in ui/app.css (goal #1 regression check PASS: 0 hex literals).
2. **CSS** (`ui/app.css`, appended after #notifBadge): `.skel-card`/`.skel-frow`/`.skel-trow`/`.skel-li`/
   `.skel-col`/`.skel-dot`/`.skel-ring`/`.skel-line` + `@keyframes skel-shimmer`/`skel-spin` +
   `@media (prefers-reduced-motion:reduce)` fallback. All values tokenized; ring uses a CSS-keyword
   mask (`black`/`transparent`, not hex). Shapes mirror the real panels exactly (.gtile card grid,
   .frow-h dashed rows, .aev mono timeline, #filesList li rows) => zero layout shift on content load.
3. **Builder** (`ui/icons.js`): `UI.skeleton(kind,n)` + `UI.sk(container,kind,n,onlyIfEmpty)` registered
   on the UI namespace (both attach + create branches). Row builder `_skRow` emits per-kind shapes.
4. **Wiring (all 4 named panels)**:
   - Fleet -> ⚠missing:core.js `fleetUpdate()`: `UI.sk($("fleetBody"),"fleet",3,true)` at fetch start; cleared on success/empty/catch.
   - Activity timeline -> ⚠missing:core.js `actUpdate()`: `UI.sk($("actBody"),"timeline",5,true)` when a session's events load; cleared on catch.
   - Files/uploads -> ⚠missing:uploads.js `filesLoad()`: `UI.sk(list,"list",6,true)` (replaces the old plain "loading…" li); `<ul>` handled via per-`<li>` rows.
   - Goals -> ⚠missing:uploads.js `goalsLoad()`: `UI.sk($("goalsBody"),"cards",8,true)`; cleared on !ok / empty-state / catch.

## Key design decision: onlyIfEmpty guard
`sk(...,onlyIfEmpty=true)` skips injection when the container already holds content. This is what stops
the **live-polling** panels (fleet 5s, activity 2s) from flashing a skeleton on every refresh — skeleton
shows only on genuine cold load. Goals/files load once per open, so they always show it on first paint.

## Acceptance status
- [x] Skeletons for all 4 panels (fleet cards, goal list/cards, timeline, uploads) — BUILT + WIRED.
- [x] Shimmer animation + reduced-motion fallback — present.
- [x] Shape-matched to real panel CSS (no layout shift by construction: same container, same row classes).
- [x] Static verification PASS: JS braces/parens balanced in all edited fns; 0 hex in ui/app.css; UI.sk
      registered + 4 call sites confirmed. Visual proof: render_html canvas rendered all 4 shapes (this pass).
- [ ] **REMAINING LEG (CDP-gated):** live-portal capture with a simulated ~2s API delay to confirm the
      skeleton actually paints during the fetch and clears on resolve without CLS. Blocked from this Pale
      sandbox seat by the documented egress/CDP wall (memory/ops/blockers.md — NEEDS-HUMAN, non-sandbox
      White/RDP seat with Edge). NOT re-probed this pass per anti-loop rule.

=> Goal #6 is at PROGRESS (build+wired+static-verified), not yet fully verified. Do NOT --record designer 6
until the live delayed-render leg runs from a non-sandbox seat.

## Files touched (this pass)
ui/tokens.css, ui/app.css, ui/icons.js, ui/core.js, ui/uploads.js
