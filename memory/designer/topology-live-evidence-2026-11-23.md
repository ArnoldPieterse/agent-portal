# Goal #7 Fleet Topology Live Update — Evidence

Date: 2026-11-23
File: ui/topology-live.js (12927B, 352 lines)

## Verification (12/12 selfTest pass)
- rateToWidth monotonic + caps at 6px ✓
- connectionHealth: idle→healthy, busy→degraded, unknown→down, stale→down ✓
- HEALTH_COLOR has all 3 tiers ✓
- MAX_PARTICLES=120 cap ✓
- UPDATE_INTERVAL=10000ms (10s) ✓
- render() + attach() + selfTest() exported ✓

## Acceptance criteria coverage
- [x] topology updates every 10s (UPDATE_INTERVAL=10000, setInterval in render())
- [x] animations are subtle (particle count capped at 120, speed 0.003, opacity 0.7)
- [x] disconnected hosts shown with dashed red lines (stroke-dasharray='6,4' + HEALTH_COLOR.down)
- [x] performance <50ms per update frame (performance.now() guard, auto-reduces particles)

## API surface
TopologyLive.render(containerEl, opts) — full self-contained render with /api/fleet polling
TopologyLive.attach(svgEl) — attach to existing FleetTopology SVG
TopologyLive.selfTest() — 12/12
TopologyLive.rateToWidth(rate), connectionHealth(state, lastSeen), HEALTH_COLOR, FALLBACK

## Design decisions
- Particle-based flow (circles along path) rather than dash-offset: more visible at low rates, less CPU
- Health tiers reuse portal color tokens (--ok/--warn/--dot-err) for consistency
- prefers-reduced-motion: disables particles but keeps state-colored lines (accessibility)
- Fallback minimal renderer when FleetTopology not loaded (graceful degradation)
- Performance guard: if frame >50ms, progressively removes particles until <45ms
