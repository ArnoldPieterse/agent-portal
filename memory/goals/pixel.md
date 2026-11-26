# Pixel — Fleet Autonomy Convergence · Next-Cycle Goals (proposed 2026-11-26)
Round topic: **Fleet Autonomy Convergence** (Lv13 round reset, GOAL_RESET_PENDING).
Prior convergence set (2026-11-25): CLOSED at 10/10 — evidence under memory/pixel/.

This cycle moves one level up from last round's state-hardening: *navigate + share* the converged
state, extend convergence to *fleet-wide autonomy attribution*, close the deferred live-screenshot
leg, and enforce bundle discipline. All implementation (HTML/CSS/JS in ui/) — not design critique
(Designer) or backend scripts (Builder). Each is small + independently verifiable.

Pillar A — Navigate & share the converged state
1. **Convergence cross-cycle trend timeline** - In `ui/cockpit-convergence.js`, add an expandable multi-cycle score chart from `/api/convergence` history (last N cycles): line/area with per-point hover+focus tooltip (cycle #, score, mode). Verified: renders >=2 real cycles; empty state (clear "no history yet") when <2; 0 console errors; point focus order matches time order. (pointer: memory/pixel/evidence-convergence-persistence-2026-11-25.md)
2. **Intervention spike -> timeline linkage** - Clicking a point on the intervention sparkline scrolls + highlights the matching entry in `ui/cockpit-intervention-timeline.js` (and back-link). Verified: clicking N spikes scrolls to + focuses the correct timeline row; fully keyboard-accessible (Enter activates); no layout shift.
3. **Convergence snapshot export / share link** - Add "Copy JSON" + a deep-link that encodes {mode, lastUpdated, 4 metric values} into query params, wired via `ui/cockpit-metrics-export.js` (or a small new module). Verified: copied JSON parses to exactly the 4 current values; deep-link round-trips and restores the view on load; payload contains no tokens/secrets.

Pillar B — Fleet-wide autonomy attribution
4. **Per-host autonomy contribution** - In `ui/fleet_topology.js` / fleetboard, show each host's share of the overall convergence/autonomy score + flag the lowest contributor ("dragging"). Verified: contributions sum ~= overall (within 1pt); lowest flagged with an aria label; renders on real `/api/fleet` data; 0 console errors.
5. **Per-host 24h health sparkline** - Compact reduced-motion-safe trend per host card in `ui/fleet_health.js`. Verified: renders per host from existing health samples; explicit empty state when no samples; scales without clipping @375px.

Pillar C — Resilience + accessibility (new legs)
6. **Close the live CDP screenshot leg (goal #5 carry-over)** - Run the deferred @375/768 live screenshots on a non-sandbox seat and archive under `memory/pixel/`. Verified: 2 screenshots archived; no horizontal overflow; all 4 widgets visible + legible. (Static leg already done 11/11 — this is the live leg only.)
7. **Per-widget render error-boundary** - A JS exception in any `ui/cockpit-*.js` renders an inline "failed to render" card with a Retry button instead of blanking the panel; integrates with the core.js boundary. Verified: injected fault in one widget -> that widget shows the error card, all others still render; Retry re-runs cleanly; 0 uncaught errors leak to console.
8. **High-contrast / token-enforcement audit** - Zero hardcoded hex outside `ui/tokens.css` across convergence + fleet surfaces; add a pre-pin grep gate (flags `#hex` in inline styles in `ui/cockpit-*.js`). Verified: gate returns 0 violations on current tree and rejects an injected violation; tokens cover all states incl. a high-contrast variant.

Pillar D — Bundle discipline
9. **Debug-artifact purge + asset gate** - Remove the ~15MB of stray debug PNGs from `ui/` (band_*, dash_*, segA-D, plan_*, crop_top, chk); add a pre-pin check that blocks any *.png / binary >N KB landing in `ui/` again; record in log.md. Verified: ui/ asset count + size reduced; gate rejects a test .png; 0 visual regression (these PNGs are never loaded by the UI).
10. **"Since last cycle" at-a-glance delta strip** - A compact always-visible strip in the cockpit header/goal bar showing Δconvergence vs previous cycle (direction + magnitude + mode), sourced from localStorage (goal #7) so it's visible without opening the panel. Verified: shows signed Δ with direction+magnitude; auto-clears after a fresh fetch; announces on change via an sr-only live region; 0 console errors.
