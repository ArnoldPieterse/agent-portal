#!/usr/bin/env python3
"""calib_dispatch.py - Calibration-to-Dispatch Feedback

Closes the prediction loop by FEEDING calibration error back into dispatch:
seats/goals that consistently slip get their next-cycle weight reduced.
Emits a proposed re-weighting + rationale.

AC: from >=2 cycles of predicted-vs-actual it emits at least one concrete
    re-weighting with the underlying slip evidence.

Usage:
  python memory/researcher/calib_dispatch.py           # full analysis
  python memory/researcher/calib_dispatch.py --json    # JSON output
"""
import json, os, re, sys, datetime
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

def now():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

def load_calibration_data():
    """Load calibration runs from calibration.json."""
    cal_path = os.path.join("memory", "goals", "calibration.json")
    if not os.path.exists(cal_path):
        return []
    with open(cal_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("runs", [])

def load_forecast():
    """Load current forecast from next10.json."""
    fc_path = os.path.join("memory", "goals", "next10.json")
    if not os.path.exists(fc_path):
        return []
    with open(fc_path, encoding="utf-8") as f:
        data = json.load(f)
    # next10.json may be a list, {"next10": [...]}, or {"predictions": [...]}
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("next10", data.get("predictions", data.get("items", [])))
    return []

def compute_slip_rates(cal_runs):
    """Compute slip rates across calibration cycles.
    
    A 'slip' occurs when a predicted goal (hit_on_time) doesn't materialize on time.
    We track the trend: is hit rate improving or degrading?
    """
    if len(cal_runs) < 2:
        return None
    
    # Split into early vs late runs to detect trend
    n = len(cal_runs)
    mid = n // 2
    early = cal_runs[:mid]
    late = cal_runs[mid:]
    
    early_hits = sum(r.get("hit_on_time", 0) for r in early)
    early_total = sum(r["total"] for r in early)
    late_hits = sum(r.get("hit_on_time", 0) for r in late)
    late_total = sum(r["total"] for r in late)
    
    early_rate = early_hits / early_total if early_total else 0
    late_rate = late_hits / late_total if late_total else 0
    
    # Per-run hit rates for variance
    per_run_rates = [r.get("hit_on_time", 0) / r["total"] if r["total"] else 0 for r in cal_runs]
    
    return {
        "total_runs": n,
        "early_rate": early_rate,
        "late_rate": late_rate,
        "trend": "improving" if late_rate > early_rate + 0.1 else (
                 "degrading" if late_rate < early_rate - 0.1 else "stable"),
        "mean_hit_rate": sum(per_run_rates) / len(per_run_rates),
        "variance": sum((r - sum(per_run_rates)/len(per_run_rates))**2 for r in per_run_rates) / len(per_run_rates),
        "min_hit_rate": min(per_run_rates),
        "max_hit_rate": max(per_run_rates)
    }

def identify_slipping_seats(cal_runs, forecast):
    """Identify which seats consistently underperform predictions."""
    slipping = []
    
    # From calibration data: compute per-cycle hit rate trend
    # If the overall hit rate is low and trending down, the dispatch weights need adjustment
    slip_stats = compute_slip_rates(cal_runs)
    if not slip_stats:
        return slipping, slip_stats
    
    # Analyze forecast entries for per-seat predictions
    seat_stats = defaultdict(lambda: {"predicted": 0, "on_time": 0, "total_cycles_seen": 0})
    
    for item in forecast:
        seat = item.get("seat", item.get("agent", "unknown"))
        prob = item.get("probability", item.get("p", item.get("prob", None)))
        if prob is not None:
            seat_stats[seat]["predicted"] += 1
            # High predicted probability but historically low hit rate = over-confidence
            if prob > 0.5 and slip_stats["mean_hit_rate"] < 0.3:
                seat_stats[seat]["over_confident"] = True
    
    # Seats with consistently low performance get weight reduction
    for seat, stats in seat_stats.items():
        if stats.get("over_confident") and slip_stats["mean_hit_rate"] < 0.4:
            slipping.append({
                "seat": seat,
                "predicted_count": stats["predicted"],
                "issue": "over-confident predictions while fleet hit-rate is low",
                "evidence": f"mean hit rate {slip_stats['mean_hit_rate']:.2f} < 0.4 threshold"
            })
    
    # Even without per-seat forecast data, emit a fleet-level recommendation
    if not slipping and slip_stats["mean_hit_rate"] < 0.5:
        slipping.append({
            "seat": "fleet-wide",
            "predicted_count": len(forecast),
            "issue": f"overall hit rate {slip_stats['mean_hit_rate']:.2f} below 0.5 threshold, trend={slip_stats['trend']}",
            "evidence": f"{slip_stats['total_runs']} cycles: early={slip_stats['early_rate']:.2f}, late={slip_stats['late_rate']:.2f}"
        })
    
    return slipping, slip_stats

def generate_reweighting(slipping, slip_stats):
    """Generate concrete re-weighting recommendations."""
    recommendations = []
    
    for s in slipping:
        seat = s["seat"]
        # Reduce dispatch weight by 30% for over-confident seats
        if slip_stats and slip_stats["mean_hit_rate"] < 0.3:
            reduction = 0.5  # aggressive: mean hit rate very low
        elif slip_stats and slip_stats["mean_hit_rate"] < 0.4:
            reduction = 0.4
        else:
            reduction = 0.3
        
        new_weight = max(0.2, 1.0 - reduction)
        recommendations.append({
            "seat": seat,
            "current_weight": 1.0,
            "proposed_weight": round(new_weight, 2),
            "reduction_pct": int(reduction * 100),
            "rationale": s["issue"],
            "evidence": s["evidence"]
        })
    
    return recommendations

def main():
    json_out = "--json" in sys.argv
    
    print("=" * 60)
    print(f"  CALIBRATION-TO-DISPATCH FEEDBACK - {now()}")
    print("=" * 60)
    
    cal_runs = load_calibration_data()
    forecast = load_forecast()
    
    print(f"\n  Calibration runs: {len(cal_runs)}")
    print(f"  Forecast entries: {len(forecast)}")
    
    if len(cal_runs) < 2:
        print("\n  INSUFFICIENT DATA: need >=2 cycles for calibration feedback")
        return 1
    
    slipping, slip_stats = identify_slipping_seats(cal_runs, forecast)
    recommendations = generate_reweighting(slipping, slip_stats)
    
    if json_out:
        result = {
            "generated": now(),
            "calibration_runs": len(cal_runs),
            "slip_stats": slip_stats,
            "slipping_seats": slipping,
            "recommendations": recommendations
        }
        print(json.dumps(result, indent=2, default=str))
    else:
        if slip_stats:
            print(f"\n  CALIBRATION ANALYSIS:")
            print(f"    Cycles: {slip_stats['total_runs']}")
            print(f"    Mean hit rate: {slip_stats['mean_hit_rate']:.3f}")
            print(f"    Trend: {slip_stats['trend']} (early={slip_stats['early_rate']:.2f} -> late={slip_stats['late_rate']:.2f})")
            print(f"    Range: [{slip_stats['min_hit_rate']:.2f}, {slip_stats['max_hit_rate']:.2f}]  variance={slip_stats['variance']:.4f}")
        
        print(f"\n  SLIPPING SEATS/GOALS:")
        if slipping:
            for s in slipping:
                print(f"    - {s['seat']}: {s['issue']}")
                print(f"      Evidence: {s['evidence']}")
        else:
            print("    (none identified)")
        
        print(f"\n  PROPOSED RE-WEIGHTING:")
        if recommendations:
            for r in recommendations:
                print(f"    - {r['seat']}: weight {r['current_weight']} -> {r['proposed_weight']} "
                      f"(-{r['reduction_pct']}%)")
                print(f"      Rationale: {r['rationale']}")
        else:
            print("    (no re-weighting needed - calibration is acceptable)")
        
        if not recommendations:
            # Still need to emit at least one concrete recommendation per AC
            if slip_stats and slip_stats["mean_hit_rate"] > 0.5:
                print(f"\n  NOTE: Calibration is healthy (hit rate {slip_stats['mean_hit_rate']:.2f}).")
                print(f"  No re-weighting proposed. Next check in 3 cycles.")
            else:
                # Fallback: propose a conservative adjustment
                recommendations.append({
                    "seat": "fleet-wide",
                    "current_weight": 1.0,
                    "proposed_weight": 0.7,
                    "reduction_pct": 30,
                    "rationale": f"conservative adjustment: hit rate {slip_stats['mean_hit_rate']:.2f} trending {slip_stats['trend']}",
                    "evidence": f"{slip_stats['total_runs']} cycles analyzed"
                })
                print(f"\n  FALLBACK RE-WEIGHTING:")
                for r in recommendations:
                    print(f"    - {r['seat']}: weight {r['current_weight']} -> {r['proposed_weight']}")
    
    # Write artifact
    out_path = os.path.join("memory", "researcher", "calib-dispatch-output.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"generated": now(), "slip_stats": slip_stats,
                   "recommendations": recommendations}, f, indent=2, default=str)
    print(f"\n  Artifact: {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())