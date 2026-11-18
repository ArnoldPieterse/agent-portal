# Fleet Capacity Endpoint - Build Evidence (2026-11-18)

Goal: Orchestrator cycle-5 #2 - Capacity Planner Panel. This leaf covers the BACKEND half.

## What was built
`GET /api/fleet/capacity` in agent_portal.py -> `_fleet_capacity_snapshot()` (+ helper `_capacity_prior`).
Per-agent returns (all numeric):
- `tokens_per_sec` : live p50 `/api/chat` latency -> est output tok/s (capped 2..60), else model prior
- `context_pct`    : (system overhead 2k + open-goals working set ~1.2k each) / model ctx window * 100
- `saturation_hours`: remaining ctx / measured history-growth-per-hour; None when no growth signal
Fleet summary: agents_total, avg_context_pct, most_saturated, min_saturation_h.
Model priors: 27B Q8 -> (32k ctx, 14 t/s); Q4 small -> (16k ctx, 30 t/s); default (32k, 20).

## Verification (in-process, exact shipped source)
Sandbox cannot import the full module (module-level `_find_sandbox_dir()` scans C:\Users ->
WinError 5 without elevation; portal runs elevated so unaffected). Verified by extracting the
exact function source and executing it against real agents.json with stubbed deps:
- Scenario A (live /api/chat perf present): tps_source=live, saturation computed from req rate.
- Scenario B (empty perf window): tps_source=prior, saturation=None for all.
- 8/8 agents returned numeric tokens_per_sec + context_pct; model-aware pct differentiation
  confirmed (q4 16k ctx -> 85.7% vs q8 32k ctx -> 42.9% at same open-goal count).
Result: PASS.

## Status
- [x] Endpoint returns valid JSON with numeric fields for all 8 agents (verified in-process)
- [ ] Gauge strip UI in fleet tab (core.js) - NEXT increment; no /api/fleet/capacity hook exists yet
      (core.js L415 'capacity.files' is the separate /api/fleet overview endpoint, not this one).
