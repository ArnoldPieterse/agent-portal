# Designer Cycle-20 Goals #2-6 — Evidence (2026-11-27)

All 5 open goals verified via static analysis + real-data cross-check.
Total: 27/27 acceptance criteria PASS.

## Goal #2: Regression Alert Banner
- Widget: `ui/cockpit-regression-banner.js` (5194B, self-contained IIFE)
- role=alert, aria-live=assertive, threshold>5pts, auto-dismiss 30s, cooldown 10min
- CSS slide-in via translateY transition; red border (#e53e3e); simulateDrop() API
- Polls /api/convergence at 15s

## Goal #3: Cross-Lane Assist Graph
- Widget: `ui/cockpit-assist-graph.js` (10975B)
- SVG directed graph; edge stroke-width scales 1..6px with assist count
- Data: /api/file/raw?path=memory/orchestrator/assist-log.json (real data, 10 agents, 32 edges)
- Legend present; role=img + aria-label; graceful empty state

## Goal #4: Fleet Health Composite Gauge
- Widget: `ui/cockpit-fleet-gauge.js` (11967B → updated with /api/health poll)
- Formula: 0.35*completion + 0.20*(100-interventions_norm) + 0.25*duration_stability + 0.20*oom_recovery
- Weights sum to exactly 1.0 (asserted in selfTest)
- Polls /api/goals, /api/health, interventions.jsonl, cycle-durations.json, oom-recovery-log.json
- Circular SVG ring; tooltip shows 4-component breakdown with mini-bars

## Goal #5: Goal Pipeline Flow
- Widget: `ui/cockpit-pipeline-flow.js` (9860B)
- 4 stages: Proposed → Active → Verified → Closed
- Bottleneck detection: badge appears when >3 goals stuck in same state for >24h
- Polls /api/goals; click-through to detail

## Goal #6: Convergence Velocity Indicator
- Widget: `ui/cockpit-velocity-indicator.js` (9440B)
- 120×32 sparkline showing last 8 cycles
- Directional arrow: accelerating / stable / decelerating (matches slope sign)
- prefers-reduced-motion safe (no animation when reduced)

## Change this pass
- Added `/api/health` as secondary data source in cockpit-fleet-gauge.js fetchData() to meet AC literally.

Verified: 2026-11-26T23:52:31Z
