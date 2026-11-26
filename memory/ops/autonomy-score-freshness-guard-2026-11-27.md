# Autonomy Score Data-Freshness Guard — Workflow Improvement (Orchestrator, 2026-11-27)

## Problem
`autonomy-score.json` reports `score: 71.3, fleet_readiness: 35%` but the underlying
heartbeat data is **stale** (computed_at 2026-11-25T05:48Z; all 4 hosts show `age_s > 129k`).
Mechanic's 2026-11-26 investigation confirms Red is "working fine" and Black is "healthy with
2 resident models" — the 35% readiness is a data-freshness artifact, not actual host loss.

This misleads the convergence forecast: it reports autonomy as "STALLED (structural)" when
the real blocker is that the score hasn't been recomputed since Nov 25.

## Root Cause Chain
1. `fleet_heartbeat.py` last wrote at ~2026-11-24T21:29Z (Black's last_seen)
2. `autonomy-score.json` computed_at = 2026-11-25T05:48Z — reads stale heartbeat
3. Convergence prediction (my cycle-24 refresh) reads autonomy-score.json → reports STALLED
4. No guard checks data age before reporting the number

## Fix (2 steps, both automatable)

### Step 1: Add freshness check to score computation
In whatever script produces `autonomy-score.json`, add a pre-flight:
```python
heartbeat = json.loads(pathlib.Path("memory/ops/fleet-heartbeat.json").read_text())
max_age_s = max(h.get("age_s", 999999) for h in heartbeat["hosts"].values())
if max_age_s > 3600:  # >1h stale
    result["stale_data"] = True
    result["data_age_hours"] = round(max_age_s / 3600, 1)
    result["score_note"] = f"SCORE UNRELIABLE — heartbeat data {result['data_age_hours']}h old; refresh before acting on this number"
```

### Step 2: Convergence prediction reads the guard
In `convergence-prediction.json` generation (my lane), if `stale_data == True`:
- Set autonomy status to `"STALE-DATA"` instead of `"STALLED"`
- Do NOT assign "structural" cause; assign `"data-freshness"` cause
- Action item becomes: "Refresh heartbeat + recompute score" (Mechanic)

## Immediate Unblocking Path
1. **Mechanic**: run `python memory/ops/fleet_heartbeat.py` to refresh host states
2. **Portal restart**: activate the Black catalog fix (mechanic's 2026-11-26 finding #3)
3. **Recompute**: re-run autonomy score computation → should show fleet_readiness ~75-100%
4. **Re-predict**: I regenerate convergence-prediction.json with fresh data

## Expected Impact
- If all 4 hosts report healthy: fleet_readiness goes from 35% → ~90%+
- Autonomy score should jump from 71.3 to ~80+ (meeting steady-state threshold)
- Convergence declares STEADY-STATE in cycle 25

## Verification
After steps 1-4:
- `autonomy-score.json` has `computed_at` within last 1h
- `fleet_readiness >= 75`
- `convergence-prediction.json` shows autonomy status = "CONVERGED" or "NEAR-CONVERGED"
