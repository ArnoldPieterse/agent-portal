"""Convergence Trajectory Model
Fits convergence curve to steady-state from cycle history (duration, completion %, intervention count).
Predicts cycles remaining to reach steady-state criteria.

Output: memory/ops/convergence-prediction.json
"""
import json, math, pathlib, sys
from datetime import datetime, timezone

OPS = pathlib.Path("memory/ops")

# Steady-state criteria (aligned with Archivist SSOT definition)
STEADY_STATE = {
    "autonomy_score_min": 80.0,       # autonomy score >= 80
    "max_interventions_per_cycle": 1.0,  # avg interventions per cycle <= 1
    "max_duration_hours": 36.0,       # cycle duration <= 36h (stable)
}

def load_jsonl(path):
    if not path.exists(): return []
    records = []
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        line = line.strip()
        if line:
            try: records.append(json.loads(line))
            except: pass
    return records

def load_json(path, default=None):
    if not path.exists(): return default
    try: return json.loads(path.read_text(encoding="utf-8"))
    except: return default

def collect_cycle_data():
    """Gather per-cycle metrics from available sources."""
    cycles = {}
    
    # From cycle-durations.jsonl
    for rec in load_jsonl(OPS / "cycle-durations.jsonl"):
        c = rec.get("cycle")
        if c:
            cycles.setdefault(c, {})["duration_hours"] = rec.get("duration_hours")
            cycles[c]["start_date"] = rec.get("start_date")
            cycles[c]["end_date"] = rec.get("end_date")
    
    # From human-interventions.jsonl - count per cycle
    for rec in load_jsonl(OPS / "human-interventions.jsonl"):
        c = rec.get("cycle")
        if c:
            cycles.setdefault(c, {})
            cycles[c]["interventions"] = cycles[c].get("interventions", 0) + 1
    
    # From efficiency-index.jsonl
    for rec in load_jsonl(OPS / "efficiency-index.jsonl"):
        c = rec.get("cycle")
        if c:
            cycles.setdefault(c, {})["efficiency_index"] = rec.get("efficiency_index")
    
    # From autonomy-score.json (latest snapshot applies to most recent cycle)
    as_data = load_json(OPS / "autonomy-score.json")
    if as_data and "score" in as_data:
        max_cycle = max(cycles.keys()) if cycles else 0
        cycles.setdefault(max_cycle, {})["autonomy_score"] = as_data["score"]
    
    # From cycle-efficiency.json (may have velocity data)
    ce = load_json(OPS / "cycle-efficiency.json")
    if ce and isinstance(ce, dict):
        for k in ("velocity_goals_per_pass", "rework_rate"):
            if k in ce:
                max_cycle = max(cycles.keys()) if cycles else 0
                cycles.setdefault(max_cycle, {})[k] = ce[k]
    
    return cycles

def fit_exponential_decay(points, steady_state):
    """Fit y(t) = ss + (y0 - ss) * exp(-k*t) to points.
    Returns (k, y0, r_squared) or None if insufficient data.
    points: list of (t, y) where t is cycle index, y is the metric value.
    steady_state: target value to converge toward.
    """
    if len(points) < 2:
        return None
    
    # Linearize: ln(y - ss) = ln(y0 - ss) - k*t  (when y > ss)
    # Or for convergence FROM above: ln(ss - y) won't work; use log-space
    # More robust: nonlinear fit via least squares on the exponential form
    
    # Simple approach: try to find k that minimizes residual
    t_vals = [p[0] for p in points]
    y_vals = [p[1] for p in points]
    
    if len(points) < 2 or all(abs(y - steady_state) < 0.01 for y in y_vals):
        return None
    
    # If all values are below steady state (converging upward), use:
    # y(t) = ss - (ss - y0) * exp(-k*t)
    converging_up = all(y <= steady_state for y in y_vals)
    
    best_k, best_r2 = None, -1
    for k_candidate in [x * 0.05 for x in range(1, 200)]:  # k from 0.05 to 10
        predictions = []
        if converging_up:
            y0 = y_vals[0]
            for t in t_vals:
                pred = steady_state - (steady_state - y0) * math.exp(-k_candidate * t)
                predictions.append(pred)
        else:
            y0 = y_vals[0]
            for t in t_vals:
                pred = steady_state + (y0 - steady_state) * math.exp(-k_candidate * t)
                predictions.append(pred)
        
        # R-squared
        mean_y = sum(y_vals) / len(y_vals)
        ss_tot = sum((y - mean_y)**2 for y in y_vals)
        ss_res = sum((y - p)**2 for y, p in zip(y_vals, predictions))
        if ss_tot < 1e-10: continue
        r2 = 1 - ss_res / ss_tot
        if r2 > best_r2:
            best_r2 = r2
            best_k = k_candidate
    
    if best_k is None or best_r2 < 0.0:
        return None
    
    y0 = y_vals[0]
    return {"k": best_k, "y0": y0, "r_squared": round(best_r2, 4)}

def predict_cycles_to_target(current_value, steady_state, k, direction):
    """Given exponential model y(t) = ss + (y0 - ss)*exp(-k*t), find t when |y - ss| < threshold."""
    if k <= 0: return None
    # We want: |current - ss| * exp(-k * dt) < tolerance
    # => dt > ln(|current - ss| / tolerance) / k
    diff = abs(current_value - steady_state)
    if diff < 1e-6: return 0
    # Use 5% of steady-state as convergence threshold
    tolerance = abs(steady_state) * 0.05 if steady_state != 0 else 0.5
    if diff <= tolerance: return 0
    dt = math.log(diff / tolerance) / k
    return max(0, math.ceil(dt))

def main():
    cycles = collect_cycle_data()
    if not cycles:
        print("ERROR: No cycle data found")
        sys.exit(1)
    
    sorted_cycles = sorted(cycles.keys())
    n_cycles = len(sorted_cycles)
    
    # --- Metric 1: Duration convergence (target: <= max_duration_hours) ---
    dur_points = [(i, cycles[c]["duration_hours"]) for i, c in enumerate(sorted_cycles) 
                  if "duration_hours" in cycles[c]]
    dur_target = STEADY_STATE["max_duration_hours"]
    
    # For duration, convergence means getting SHORT (or stable below threshold)
    dur_fit = None
    if len(dur_points) >= 2:
        # Check if durations are already at target
        latest_dur = dur_points[-1][1]
        if latest_dur <= dur_target:
            dur_fit = {"k": float("inf"), "already_converged": True, "r_squared": 1.0}
        else:
            # Fit decay toward target (duration should be DECREASING)
            dur_fit = fit_exponential_decay(dur_points, dur_target)
    
    # --- Metric 2: Intervention rate convergence (target: <= max_per_cycle) ---
    total_interventions = sum(cycles[c].get("interventions", 0) for c in sorted_cycles)
    avg_interventions = total_interventions / n_cycles if n_cycles > 0 else 0
    int_target = STEADY_STATE["max_interventions_per_cycle"]
    
    # Per-cycle intervention count (sparse - many cycles have 0)
    int_points = [(i, cycles[c].get("interventions", 0)) for i, c in enumerate(sorted_cycles)]
    int_fit = None
    if len(int_points) >= 2:
        if avg_interventions <= int_target:
            int_fit = {"k": float("inf"), "already_converged": True, "r_squared": 1.0}
        else:
            # Interventions should decrease; fit toward 0 or target
            int_fit = fit_exponential_decay(int_points, int_target)
    
    # --- Metric 3: Autonomy score convergence (target: >= autonomy_score_min) ---
    as_points = [(i, cycles[c]["autonomy_score"]) for i, c in enumerate(sorted_cycles)
                 if "autonomy_score" in cycles[c]]
    as_target = STEADY_STATE["autonomy_score_min"]
    
    as_fit = None
    current_autonomy = None
    if as_points:
        current_autonomy = as_points[-1][1]
        if current_autonomy >= as_target:
            as_fit = {"k": float("inf"), "already_converged": True, "r_squared": 1.0}
        elif len(as_points) >= 2:
            as_fit = fit_exponential_decay(as_points, as_target)
    
    # --- Predict cycles remaining per metric ---
    predictions = {}
    
    # Duration
    if dur_fit and not dur_fit.get("already_converged"):
        latest_dur = dur_points[-1][1]
        pred_d = predict_cycles_to_target(latest_dur, dur_target, dur_fit["k"], "down")
        predictions["duration"] = {"current": latest_dur, "target": dur_target, 
                                   "cycles_remaining": pred_d, "confidence": dur_fit.get("r_squared", 0.3)}
    elif dur_fit and dur_fit.get("already_converged"):
        predictions["duration"] = {"current": dur_points[-1][1] if dur_points else None, 
                                   "target": dur_target, "cycles_remaining": 0, "confidence": 1.0}
    else:
        predictions["duration"] = {"current": dur_points[-1][1] if dur_points else None,
                                   "target": dur_target, "cycles_remaining": None, "confidence": 0.0,
                                   "note": "insufficient data"}
    
    # Interventions - use cumulative average trend (more stable for sparse binary data)
    cum_avg_points = []
    running_sum = 0
    for i, c in enumerate(sorted_cycles):
        running_sum += cycles[c].get("interventions", 0)
        cum_avg_points.append((i + 1, running_sum / (i + 1)))
    
    if avg_interventions <= int_target:
        predictions["interventions"] = {"current": round(avg_interventions, 3), "target": int_target,
                                        "cycles_remaining": 0, "confidence": 0.9}
    elif avg_interventions <= int_target * 1.2:
        # Near-converged: within 20% of target, use zero-intervention projection
        x_needed = max(0, math.ceil(total_interventions / int_target - n_cycles)) if int_target > 0 else None
        predictions["interventions"] = {"current": round(avg_interventions, 3), "target": int_target,
                                        "cycles_remaining": x_needed, 
                                        "confidence": 0.7,
                                        "method": "near-converged (within 20% of target); zero-intervention projection"}
    elif len(cum_avg_points) >= 2 and cum_avg_points[-1][1] > cum_avg_points[0][1]:
        # Cumulative avg is rising (bad) - can't converge with current trend
        pred_i = None
        predictions["interventions"] = {"current": round(avg_interventions, 3), "target": int_target,
                                        "cycles_remaining": None, "confidence": 0.2,
                                        "note": "cumulative avg trending up; no convergence without behavior change"}
    elif len(cum_avg_points) >= 2:
        # Cumulative avg is flat or declining - use gap to estimate
        gap = avg_interventions - int_target
        # Each additional cycle with 0 interventions reduces avg by ~gap/(n+1)
        # Solve: (total + 0*x) / (n+x) <= target => x >= total/target - n
        x_needed = max(0, math.ceil(total_interventions / int_target - n_cycles)) if int_target > 0 else None
        predictions["interventions"] = {"current": round(avg_interventions, 3), "target": int_target,
                                        "cycles_remaining": x_needed, 
                                        "confidence": 0.6 if x_needed is not None and x_needed <= 3 else 0.4,
                                        "method": "zero-intervention projection"}
    else:
        predictions["interventions"] = {"current": round(avg_interventions, 3), "target": int_target,
                                        "cycles_remaining": None, "confidence": 0.0,
                                        "note": "insufficient data"}
    
    # Autonomy - handle single-point case with heuristic
    if current_autonomy and current_autonomy >= as_target:
        predictions["autonomy"] = {"current": current_autonomy, "target": as_target,
                                   "cycles_remaining": 0, "confidence": 1.0}
    elif as_fit and not as_fit.get("already_converged"):
        pred_a = predict_cycles_to_target(current_autonomy, as_target, as_fit["k"], "up")
        predictions["autonomy"] = {"current": current_autonomy, "target": as_target,
                                   "cycles_remaining": pred_a, "confidence": as_fit.get("r_squared", 0.3)}
    elif current_autonomy and len(as_points) == 1:
        # Single point: use heuristic based on gap and observed improvement rate
        gap = as_target - current_autonomy
        # Heuristic: ~5 pts/cycle improvement is optimistic, ~2.5 is conservative
        pred_optimistic = math.ceil(gap / 5.0)
        pred_conservative = math.ceil(gap / 2.5)
        predictions["autonomy"] = {"current": current_autonomy, "target": as_target,
                                   "cycles_remaining_range": [pred_optimistic, pred_conservative],
                                   "cycles_remaining": pred_conservative,
                                   "confidence": 0.3,
                                   "note": f"single data point; range {pred_optimistic}-{pred_conservative} cycles based on heuristic improvement rate"}
    else:
        predictions["autonomy"] = {"current": current_autonomy, "target": as_target,
                                   "cycles_remaining": None, "confidence": 0.0,
                                   "note": "no data available"}
    
    # --- Overall prediction ---
    known_predictions = [p["cycles_remaining"] for p in predictions.values() if p.get("cycles_remaining") is not None]
    overall_cycles = max(known_predictions) if known_predictions else None
    
    # If some metrics are unknown, note it explicitly
    n_unknown = sum(1 for p in predictions.values() if p.get("cycles_remaining") is None)
    overall_confidence = "HIGH" if n_unknown == 0 else ("MEDIUM" if n_unknown == 1 else "LOW")
    
    # Convergence health: fraction of metrics already converged
    n_converged = sum(1 for p in predictions.values() if p.get("cycles_remaining") == 0)
    convergence_pct = (n_converged / len(predictions)) * 100 if predictions else 0
    
    result = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "steady_state_criteria": STEADY_STATE,
        "cycles_analyzed": n_cycles,
        "cycle_numbers": sorted_cycles,
        "per_metric": predictions,
        "overall_prediction": {
            "cycles_to_steady_state": overall_cycles,
            "confidence": overall_confidence,
            "current_cycle": max(sorted_cycles),
            "predicted_steady_state_cycle": (max(sorted_cycles) + overall_cycles) if overall_cycles is not None else None,
            "convergence_pct": round(convergence_pct, 1),
            "metrics_converged": n_converged,
            "metrics_total": len(predictions),
            "metrics_unknown": n_unknown,
        },
        "data_quality": {
            "duration_points": len(dur_points),
            "intervention_points": len(int_points),
            "autonomy_points": len(as_points),
            "sparse_data_warning": n_cycles < 5,
        },
    }
    
    out = OPS / "convergence-prediction.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"\n=== Convergence Trajectory Model ===")
    print(f"Cycles analyzed: {n_cycles} ({sorted_cycles})")
    for metric, pred in predictions.items():
        cur = pred.get("current", "?")
        tgt = pred.get("target", "?")
        rem = pred.get("cycles_remaining", "?")
        conf = pred.get("confidence", 0)
        status = "CONVERGED" if rem == 0 else f"{rem} cycles remaining" if rem is not None else "UNKNOWN (insufficient data)"
        print(f"  {metric}: current={cur}, target={tgt} -> {status} (confidence={conf})")
    op = result["overall_prediction"]
    cts = op['cycles_to_steady_state']
    if cts is None:
        print(f"\nOVERALL: INDETERMINATE ({op['metrics_unknown']} of {op['metrics_total']} metrics unknown)")
    else:
        print(f"\nOVERALL: <= {cts} cycles to steady-state "
              f"(convergence {op['convergence_pct']}%, confidence={op['confidence']})")
    if result["data_quality"]["sparse_data_warning"]:
        print("WARNING: Sparse data (<5 cycles) - predictions are low-confidence estimates")

if __name__ == "__main__":
    main()
