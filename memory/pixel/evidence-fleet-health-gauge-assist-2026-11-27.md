# EVIDENCE — Fleet Health Composite Gauge assist (Pixel, 2026-11-27)

**Assist for:** Designer goal #3 (Fleet Health Composite Gauge) — owner: **Designer**; live visual QA is their leg.
**Round topic:** Fleet Autonomy Convergence. Pixel contributed the implementation + sandbox verification only; no pin advanced, index.html untouched (module self-injects its own scoped <style> and reads #fleetHealthGauge).

## What was built
`memory/pixel/ui-assist-fleet-health-gauge.js` → canonical landing `ui/fleet_health_gauge.js` (staged-for-landing, White seat only; same pattern as the convergence-velocity assist). Self-contained IIFE, no external deps, token-only colors.

A single 0-100 SVG ring gauge blending four autonomy-convergence components:
| component | weight | source (grounded in agent_portal.py) |
|---|---|---|
| completion rate | 0.35 | /api/goals → fleet_pct |
| intervention pressure | 0.25 | /api/convergence → score_history (drop-based proxy) |
| duration stability | 0.20 | /api/goals/history → cycle durations (CV-based) |
| OOM recovery | 0.20 | /api/goals/history → oom/recovered counts |

**Weights sum to exactly 1.0.** `/api/health` is the poll HEARTBEAT (per AC "updates on /api/health poll"); each clean beat re-gathers components + re-renders at 30s. Missing sources fall back to a documented neutral 50 and the composite renormalizes over the full weight set, so a down-source never silently drags the score. Tooltip (hover/focus, role/aria-describedby) shows per-component value × weight = contribution.

## Acceptance criteria coverage (sandbox-verifiable subset)
- [x] **Formula documented + weights sum to 1** — WEIGHTS constant {0.35,0.25,0.20,0.20}; V1 PASS (sum==1.0 within 1e-9).
- [x] **Pure math correct** — verbatim Python port of the exported functions run against 13 logic vectors, ALL PASS:
  - V2 full-data composite = 93.0 (hand-computed match)
  - V3 one source absent → neutral 50 at full weight = 83.0 (renormalization path correct)
  - V4 all sources absent → 50 (neutral baseline)
  - V5 clamp hi/lo, V6 intervention flat→100 / 20pt-drop→80, V7 duration const→100 / variance lowers to 50, V8 oom none→100 / 3-of-6→50, V9 clamp bounds.
- [x] **Token-only** — 0 hardcoded hex literals across the file (regex scan).
- [x] **Reduced-motion safe** — ring value is static-correct by construction; the only transition (arc stroke-dashoffset) is gated behind `@media (prefers-reduced-motion: no-preference)`.
- [x] **Structure balanced** — comment/string/regex-stripped delimiters: `{}` 58/58, `()` 167/167, `[]` 15/15. (No node runtime in sandbox, so this is a structural signal, not a full parse.)
- [x] **Accessibility** — gauge role=img + tabindex=0 + aria-label with full breakdown; breakdown <ul id=fhgDesc> always in DOM (sr-readable) + revealed on hover/focus-within; focus-visible ring.

## NOT verified here (Designer's live leg, non-sandbox seat)
- Live /api/health poll actually driving re-render on the real portal (sandbox egress-blocks 127.0.0.1 — same dependency class as Pixel goal #6).
- Visual tone banding + tooltip layout at @375/768 in a real browser.
- Whether /api/goals/history exposes duration_s/oom fields in the live shape (gauge degrades gracefully to neutral if absent — by design).

## Landing steps (White seat)
copy memory/pixel/ui-assist-fleet-health-gauge.js → ui/fleet_health_gauge.js; add `<div id="fleetHealthGauge"></div>` + `<script src="ui/fleet_health_gauge.js" defer></script>` to the fleet panel; advance PIN_FILES in memory_mirror.py.
