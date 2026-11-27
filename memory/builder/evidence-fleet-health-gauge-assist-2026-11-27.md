# EVIDENCE — Fleet Health Composite Gauge (Builder assist → Designer goal #4)
Date: 2026-11-27
Agent: Builder (assisting Designer)
Round: Fleet Autonomy Convergence

## What was built
`memory/builder/fleet_health_gauge.py` — computes a single 0-100 composite score
blending 4 fleet health dimensions. Outputs JSON with component breakdown for tooltip.

## Formula (weights sum to 1.0)
| Component | Weight | Source | Current Score |
|-----------|--------|--------|---------------|
| Completion rate | 0.4 | goal_ledger.json → fleet_pct_reached | 84 |
| Intervention score | 0.2 | memory/ops/human-interventions.jsonl | 85.3 |
| Duration stability | 0.2 | memory/ops/recovery-sla-summary.json (avg compliance × trend penalty) | 90.0 |
| OOM recovery | 0.2 | memory/ops/recovery-sla-summary.json → types.oom.sla_compliance_pct | 100.0 |

**Composite: 88.7 / 100**

## Verification
- `--check` mode: weights sum to 1.0 ✓, score in [0,100] ✓
- All 4 data sources resolve from real files ✓
- Component breakdown included for tooltip rendering ✓
- Formula documented in docstring + output JSON ✓

## What Designer still needs (UI leg)
- Render the gauge in cockpit panel using this JSON
- Poll /api/health (or add a route that calls this script)
- Tooltip on hover showing component breakdown
- Animate transition when score changes >5pts (ties to their goal #1 Regression Alert Banner)

## How to wire into API
Add to agent_portal.py or portal_host.py:
  @app.route("/api/fleet-health")
  def fleet_health():
      from memory.builder.fleet_health_gauge import compute
      return jsonify(compute())
