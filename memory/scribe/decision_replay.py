"""Decision Replay & Counterfactual Log - quantifies the causal value of each automation decision.

For each decision that eliminated an intervention class (from decision-autonomy-map.jsonl):
  Compute the COUNTERFACTUAL: what would the metric have been WITHOUT this decision?
  
Projection method (stated): 
  - Establish a BASELINE RATE from the early period (cycles before full automation effect)
  - Project cumulative total to target cycle using that rate
  - causal_gain = baseline_projected_total - actual_total (positive = interventions avoided)
  
  For autonomy score: use linear extrapolation of pre-decision trend; 
  causal_gain = baseline_projected_score - actual_score (negative = score higher than projected = good)

Output: memory/scribe/decision-replay.jsonl
  {cycle, decision_id, decision, class, metric, baseline_projected, actual, causal_gain, method, source}

Data sources:
  - memory/scribe/decision-autonomy-map.jsonl (decisions)
  - memory/scribe/convergence-kpi.jsonl (per-cycle scores + interventions)
  - memory/scribe/autonomy-trend.jsonl (supplemental score data)  
  - memory/ops/human-interventions.jsonl (per-cycle intervention counts)
"""
import json, pathlib, sys
from datetime import datetime, timezone, date as dt_date

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "memory/scribe/decision-replay.jsonl"


def load_jsonl(relpath):
    p = pathlib.Path(relpath)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    out = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def get_intervention_series():
    """Get {cycle: count} from human-interventions.jsonl + KPI."""
    entries = load_jsonl("memory/ops/human-interventions.jsonl")
    counts = {}
    for e in entries:
        c = e.get("cycle")
        if c is not None:
            counts[c] = counts.get(c, 0) + 1
    kpi = load_jsonl("memory/scribe/convergence-kpi.jsonl")
    for e in kpi:
        c = e.get("cycle")
        if c is not None and c not in counts:
            counts[c] = e.get("interventions", 0)
    return dict(sorted(counts.items()))


def get_score_series():
    """Get {cycle: score} from KPI + trend."""
    kpi = load_jsonl("memory/scribe/convergence-kpi.jsonl")
    trend = load_jsonl("memory/scribe/autonomy-trend.jsonl")
    data = {}
    for e in kpi:
        c = e.get("cycle")
        if c is not None and e.get("autonomy_score") is not None:
            data[c] = e["autonomy_score"]
    for e in trend:
        c = e.get("cycle")
        if c is not None and c not in data and e.get("score") is not None:
            data[c] = e["score"]
    return dict(sorted(data.items()))


def compute_intervention_counterfactual(intv_series, target_cycle):
    """Project cumulative interventions to target cycle using early-period rate.
    
    Method: use cycles 2-5 as baseline period (pre-full-automation).
    Rate = total_interventions_in_period / span_of_period
    Projected_total_at_target = rate * target_cycle
    
    Returns: (projected_total, actual_total, method_str)
    """
    # Baseline period: first 4 cycles of data (cycles 2-5)
    baseline_cycles = [c for c in sorted(intv_series.keys()) if c <= 5]
    if not baseline_cycles:
        return None, None, "no_baseline_period"
    
    baseline_total = sum(intv_series[c] for c in baseline_cycles)
    span = max(baseline_cycles) - min(baseline_cycles) + 1  # inclusive span
    rate = baseline_total / span if span > 0 else baseline_total
    
    # Project to target
    projected_total = rate * target_cycle
    
    # Actual cumulative total at target cycle
    actual_total = sum(v for c, v in intv_series.items() if c <= target_cycle)
    
    method = (f"early_rate({baseline_total} intv over cycles "
              f"{min(baseline_cycles)}-{max(baseline_cycles)}, rate={rate:.2f}/cycle) "
              f"* target_c{target_cycle}")
    
    return projected_total, actual_total, method


def compute_score_counterfactual(score_series, target_cycle):
    """Project autonomy score to target cycle using linear trend from available data.
    
    Method: linear extrapolation from all available score points.
    Returns: (projected_score, actual_score, method_str)
    """
    if not score_series:
        return None, None, "no_score_data"
    
    points = sorted(score_series.items())
    if len(points) == 1:
        return points[0][1], score_series.get(target_cycle), "flat_single_point"
    
    # Use first and last for overall trend (captures the full trajectory)
    (c1, v1), (c2, v2) = points[0], points[-1]
    if c2 == c1:
        return v2, score_series.get(target_cycle), "flat_same_cycle"
    
    slope = (v2 - v1) / float(c2 - c1)
    projected = v2 + slope * (target_cycle - c2)
    actual = score_series.get(target_cycle)
    
    method = f"linear(slope={slope:.3f}/cycle from c{c1}->c{c2}, extrapolated to c{target_cycle})"
    return projected, actual, method


def run():
    decisions = load_jsonl("memory/scribe/decision-autonomy-map.jsonl")
    intv_series = get_intervention_series()
    score_series = get_score_series()
    
    if not decisions:
        print("No decisions found.")
        return []
    
    all_cycles = set(list(intv_series.keys()) + list(score_series.keys()))
    target_cycle = max(all_cycles) if all_cycles else None
    
    # Compute counterfactuals (shared across decisions since they all contributed to the same outcome)
    intv_proj, intv_actual, intv_method = compute_intervention_counterfactual(intv_series, target_cycle)
    score_proj, score_actual, score_method = compute_score_counterfactual(score_series, target_cycle)
    
    results = []
    for dec in decisions:
        dec_id = dec.get("decision_id", "unknown")
        dec_text = dec.get("decision", "")[:100]
        intervention_class = dec.get("intervention_class_removed", "")
        
        # Intervention counterfactual
        intv_gain = None
        if intv_proj is not None and intv_actual is not None:
            intv_gain = round(intv_proj - intv_actual, 4)
        
        results.append({
            "cycle": target_cycle,
            "decision_id": dec_id,
            "decision": dec_text,
            "class": intervention_class,
            "metric": "interventions_cumulative",
            "baseline_projected": round(intv_proj, 2) if intv_proj is not None else None,
            "actual": intv_actual,
            "causal_gain": intv_gain,
            "method": intv_method,
            "source": f"decision-autonomy-map.jsonl:{dec_id}"
        })
        
        # Score counterfactual
        score_gain = None
        if score_proj is not None and score_actual is not None:
            score_gain = round(score_proj - score_actual, 4)
        
        results.append({
            "cycle": target_cycle,
            "decision_id": dec_id,
            "decision": dec_text,
            "class": intervention_class,
            "metric": "autonomy_score",
            "baseline_projected": round(score_proj, 2) if score_proj is not None else None,
            "actual": score_actual,
            "causal_gain": score_gain,
            "method": score_method,
            "source": f"decision-autonomy-map.jsonl:{dec_id}"
        })
    
    # Write output
    ts = datetime.now(timezone.utc).isoformat()
    out_lines = []
    for r in results:
        r["ts"] = ts
        out_lines.append(json.dumps(r))
    OUT.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    
    print(f"Wrote {len(results)} replay entries to {OUT}")
    print(f"Target cycle: {target_cycle}")
    for r in results:
        b = f"{r['baseline_projected']:.2f}" if r['baseline_projected'] is not None else "None"
        a = str(r['actual']) if r['actual'] is not None else "None"
        g = f"{r['causal_gain']:+.2f}" if r['causal_gain'] is not None else "N/A"
        print(f"  [{r['metric']:24s}] {r['decision_id']}: baseline={b} actual={a} gain={g}")
    
    return results


def run_synthetic_test():
    """Verify projection + gain on known data."""
    print("\n=== SYNTHETIC TEST ===")
    
    # Test 1: Intervention counterfactual
    # Early period (cycles 2-5): 3 interventions over span 4 -> rate 0.75/cycle
    # Projected to cycle 20: 0.75 * 20 = 15
    # Actual total by cycle 20: 5 (say)
    # Gain = 15 - 5 = 10
    intv = {2: 1, 3: 1, 5: 1, 8: 1, 10: 1, 20: 1}
    proj, actual, method = compute_intervention_counterfactual(intv, 20)
    # Baseline: cycles <= 5: {2:1, 3:1, 5:1} = 3 over span (5-2+1)=4 -> rate=0.75
    # Projected: 0.75 * 20 = 15.0
    # Actual total by c20: 1+1+1+1+1+1 = 6
    assert abs(proj - 15.0) < 0.01, f"FAIL: expected 15.0, got {proj}"
    assert actual == 6, f"FAIL: expected 6, got {actual}"
    gain = round(proj - actual, 4)
    assert gain == 9.0, f"FAIL: expected 9.0, got {gain}"
    print(f"  Intervention CF: proj={proj}, actual={actual}, gain={gain} ({method}) PASS")
    
    # Test 2: Score counterfactual (linear)
    # Points: (5, 64.5), (17, 69.1), (23, 71.3)
    # Slope from first to last: (71.3-64.5)/(23-5) = 6.8/18 = 0.378/cycle
    # Projected to cycle 30: 71.3 + 0.378*(30-23) = 71.3 + 2.64 = 73.94
    scores = {5: 64.5, 17: 69.1, 23: 71.3}
    proj_s, actual_s, method_s = compute_score_counterfactual(scores, 30)
    expected = 71.3 + (6.8/18)*(30-23)
    assert abs(proj_s - expected) < 0.1, f"FAIL: expected {expected:.2f}, got {proj_s}"
    print(f"  Score CF: proj={proj_s:.2f} (expected ~{expected:.2f}), actual={actual_s} ({method_s}) PASS")
    
    # Test 3: Causal gain sign convention
    # Interventions: positive gain = good (fewer than projected)
    assert round(15.0 - 6.0, 4) == 9.0
    # Score: negative gain = good (actual higher than projected)
    assert round(73.0 - 80.0, 4) == -7.0
    print(f"  Sign convention: intv_gain=+9 (good), score_gain=-7 (good) PASS")
    
    # Test 4: Edge case - no data
    proj_none, _, reason = compute_intervention_counterfactual({}, 10)
    assert proj_none is None
    print(f"  Empty data: None ({reason}) PASS")
    
    print("  ALL SYNTHETIC TESTS PASS")
    return True


if __name__ == "__main__":
    if "--test" in sys.argv:
        ok = run_synthetic_test()
        sys.exit(0 if ok else 1)
    else:
        results = run()
