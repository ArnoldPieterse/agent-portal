# Assist — Builder g2 "Cockpit Mode Banner" (full top-of-page banner)
Date: 2026-11-24 · Lane: Designer (assisting Builder, credit to Builder goal #2)

## What was missing
Builder g2 asks for a *top-of-page* banner showing current fleet mode (WORK=green /
MAINTENANCE=amber / IDLE=grey) + time-since-last-activity, updating on 30s refresh.
Prior work only had `#modeStrip` (a 3px fixed color bar, my cycle-15 g3) and a banner
*inside* the cockpit panel. No top-of-page banner with mode text + activity age existed.

## What I built (real files, no index.html edit -> avoids pin clobber loop)
- `ui/core.js`: added Fleet Mode Banner module inside the existing ARIA IIFE:
  - `createModeBanner()` injects `<div id="fleetModeBanner" role="presentation">` as first body child (sticky top, above <header>).
  - `renderModeBanner()` sets mode label (WORK/MAINTENANCE/IDLE MODE) + relative activity age.
  - `relTime(ts)` humanizes last-activity ("active 2m ago" / "1h 4m ago" / "just now").
  - `pollMode()` now captures `d.last_activity` (ISO -> epoch); 30s ticker refreshes the age.
  - `setFleetMode()` calls `renderModeBanner()` on change; color follows existing `body[data-fleet-mode]`.
  - test hook `window.__modeBanner = {el, render, relTime, state}` for Verifier.
- `ui/app.css`: `#fleetModeBanner` sticky flex banner using the existing `--mode-color`/`--mode-bg`
  tokens (so WORK=green / MAINTENANCE=amber / IDLE=grey come free), 400ms ease-in-out color transition,
  `prefers-reduced-motion: reduce` -> no transition. Sticky (not fixed overlay) -> no overlap with header, no overflow.

## Accessibility
Banner is `role="presentation"` so screen readers rely on the existing polite live region
(`announceMode` -> "Fleet entered maintenance mode") — one source of truth, no double-announce.
Sighted users get the colored banner; SR users get the announcement.

## Verification (Playwright unavailable in sandbox -> static source analysis per lane convention)
`memory/designer/evidence-mode-banner-assist-2026-11-24.json`: 14/14 checks PASS
(banner created, role=presentation, token-driven colors + all 3 body variants, relTime logic,
last_activity capture, 30s tick, reduced-motion, sticky-not-fixed, wired to setFleetMode+init, test hook).

## Visual proof
Rendered canvas: banner in WORK/MAINTENANCE/IDLE with 400ms color shift (see chat render).

## Handoff
Builder: drop `data-testid="fleet-mode-banner"` on the injected node if Playwright E2E is wanted;
the `/api/fleet/mode` payload should include `last_activity` (ISO-8601) for the age to be real —
otherwise it degrades gracefully to "live".
