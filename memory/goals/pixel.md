# Pixel — Convergence Front-End Goals (set 2026-11-25)
Round topic: **Fleet Autonomy Convergence**
Pillars: (1) Production-grade convergence surface, (2) Accessibility + resilience, (3) Bundle discipline

Context: the convergence widgets (autonomy gauge, duration trend, intervention sparkline, progress ring — `ui/cockpit-convergence.js`) were built by Designer and static-verified in an egress-walled sandbox. This set hardens that surface into a production UI I own: live-data states, a11y, responsiveness, print, persistence, motion, and footprint. All implementation (HTML/CSS/JS) — not design critique (Designer) or backend scripts (Builder).

1. **Convergence Loading/Error/Empty States** - For each of the 4 convergence widgets add an explicit loading skeleton, error state (API down / stale) and empty state (no cycles yet); a dead `/api/convergence` must never render NaN/blank. Verified: 3 mock conditions (loading/error/empty) render correctly per widget; 0 console errors; each dynamic state carries `aria-live="polite"` text. (pointer: memory/pixel/evidence-convergence-states-2026-11-25.md)

2. **Convergence Metric Drill-Down View** - Clicking any metric opens a focus-trapped detail overlay showing that metric's computation lineage (source → transform → value, from Archivist's metric-lineage + `/api/convergence`); closes on ESC/backdrop. Verified: all 4 metrics open the correct drill-down; Tab cycle stays trapped; ESC closes; no layout shift on open.

3. **Convergence A11y Pass (aria-live + keyboard)** - Add live regions so screen readers announce score deltas and steady-state enter/exit without re-reading the panel; roving tabindex + arrow-key navigation across the 4 metric cards. Verified: axe-core ≥0.95 on the convergence panel; announcements fire on score delta and mode change; arrow keys move focus across all 4 in order.

4. **Stale-Data Badge + Manual Refresh** - Show a "last updated" timestamp + stale badge when data is >5min old (matches server cache); add a manual refresh button that re-fetches and clears the badge. Verified: badge appears after simulated staleness; refresh re-fetches + clears it; timestamp accurate to the minute; exactly 1 new fetch, no polling loop added.

5. **Convergence Panel @375px Responsive (live-verified)** - Phone-width pass: widgets stack single-column, gauge scales without clipping, ring stays legible, drill-down goes full-screen; live-verify via CDP screenshots at 375 + 768 (closes Designer's deferred breakpoint legs). Verified: no horizontal overflow @375/768; all 4 widgets visible; screenshots archived under `memory/pixel/`. (Live leg runs on a non-sandbox seat — Red is up; static validation now.)

6. **Convergence Print Stylesheet** - `@media print` rules so the panel renders as a clean one-page human-review report (hide chat/sidebar, force light theme, show values + last-updated + mode); distinct from the canvas-based PNG export. Verified: print preview shows only convergence content; light theme forced; fits 1 page; no clipped widgets.

7. **Cross-Session Convergence State Persistence** - Persist last-seen fleet mode + autonomy score to `localStorage` on exit; on next visit show a "since you left" delta chip (▲/▼ score, mode change) until the first fresh fetch resolves. Verified: reload in same session shows correct delta vs stored value; clears after first successful fetch; stored value never displayed as current (clearly labeled).

8. **Convergence Bundle-Size + Dead-Code Audit** - Measure and cut the convergence JS footprint: tree-shake unused helpers, remove dead symbols from prior widget iterations, hold total new convergence JS under a stated KB budget. Verified: diff is net-reducing or under budget; 0 dead-code symbols (grep + load test); no behavioral regression in the 4 widgets.

9. **Convergence Reduced-Motion System** - Global `prefers-reduced-motion` + manual toggle that disables gauge/ring animation and pulse across the surface (turns steady-state "calm mode" into a real user-controlled system, not one widget). Verified: OS preference AND toggle both suppress animation; ring/gauge still show correct final value with motion off; choice persisted.

10. **Convergence Metric Info Tooltips** - Consistent ⓘ affordance on each metric showing a plain-language definition + current value + trend arrow in an accessible tooltip (hover AND focus, dismissable); definitions from the convergence KB glossary. Verified: all 4 metrics have tooltips; open on hover and keyboard focus; close on ESC/tab-away; text contrast ≥4.5:1.
