# Fleet Insights API endpoint built - 2026-11-23

**Goal:** Builder #1 (Fleet Insights Dashboard) - backend prerequisite

## What was done
Added `GET /api/fleet/insights` to agent_portal.py:
- `_fleet_insights_snapshot()` helper function (inserted before `_decisions_snapshot`)
- Route in `_do_GET`: `elif p == "/api/fleet/insights"`

## Response structure
```json
{
  "ok": true,
  "capacity_forecast": [{host, metric, current, slope_per_day, days_to_breach, threshold_pct, alert, status}],
  "recent_anomalies": [{path, agent, ts, title}],
  "prediction_accuracy": {data_points, hosts_tracked, note},
  "forecast_ts": "ISO timestamp"
}
```

## Data sources
- `memory/mechanic/capacity-plan-latest.json` - forecast (from capacity_plan.py)
- `memory/*/anomaly*` files (mtime < 14 days) - recent anomalies
- `memory/mechanic/capacity_data.jsonl` - prediction accuracy baseline

## Verification
- Syntax check: PASS (ast.parse)
- Direct function call: returns correct JSON with real data (2 anomalies, 1 forecast entry, 1 data point)
- HTTP test: portal not running on Black seat (runs on White); code will be live after next mirror+restart

## Next steps for full Goal #1
1. Build UI panel (ui/insights.js or extend fleet_topology.js pattern)
2. Add toggle button in index.html (requires pin advance)
3. Chart rendering for capacity forecast (7-day trend + breach line)
