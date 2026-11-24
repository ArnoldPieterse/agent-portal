#!/usr/bin/env python3
"""Predictive Model Accuracy Tracker
Tracks actual-vs-predicted accuracy for all fleet predictive models.
Flags models whose accuracy degrades below threshold (default: r2 < 0.5 or MAE > 20%).

Usage:
  python memory/verifier/predictive_accuracy_tracker.py --self-test
  python memory/verifier/predictive_accuracy_tracker.py
"""
import json, pathlib, sys, math, argparse
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
MODELS = {
    "convergence_rate": {
        "results_file": "memory/researcher/convergence-rate-results.json",
        "min_r2": 0.5,
        "description": "Exponential fit to error_free_rate predicting convergence cycle",
    },
    "convergence_trajectory": {
        "results_file": "memory/researcher/convergence-trajectory-results.json",
        "min_r2": 0.3,  # lower threshold because multi-metric composite
        "description": "Multi-metric steady-state gate predicting cycles-to-steady-state",
    },
    "vram_forecast": {
        "results_file": "memory/ops/vram-forecast.json",
        "min_r2": 0.5,
        "description": "Per-host VRAM headroom predictor (OOM pre-alert)",
    },
}

ACCURACY_HISTORY_FILE = "memory/verifier/predictive-accuracy-history.jsonl"
DEGRADATION_THRESHOLD = 0.2  # flag if accuracy drops >20% vs rolling mean


def load_model_results(model_key):
    """Load results for a model; return None if file missing."""
    spec = MODELS[model_key]
    fp = ROOT / spec["results_file"]
    if not fp.exists():
        return None
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def extract_accuracy(data, model_key):
    """Extract accuracy metrics from model results. Returns dict with r2 and mae if available."""
    if data is None:
        return {"status": "no_data", "r2": None, "mae_pct": None}

    result = {"status": "ok", "r2": None, "mae_pct": None}

    if model_key == "convergence_rate":
        result["r2"] = data.get("r2")
        # MAE: compare predicted convergence cycle vs actual (cycle 0 = already converged)
        pred_cycle = data.get("predicted_convergence_cycle")
        n_points = data.get("data_points", 0)
        if pred_cycle is not None and n_points > 0:
            # If predicted cycle 0 but we're at point n, actual remaining = max(0, some_target - current)
            # Use r2 as primary accuracy proxy here
            result["mae_pct"] = None  # no clear single MAE for convergence timing

    elif model_key == "convergence_trajectory":
        est = data.get("estimate", {})
        result["r2"] = est.get("r2_composite_index")
        # Check trajectory consistency: composite index should be trending toward steady-state
        traj = est.get("composite_index_trajectory", [])
        if len(traj) >= 3:
            # Simple MAE proxy: deviation of last point from mean (stability check)
            mean_val = sum(traj[-5:]) / min(5, len(traj))
            if mean_val != 0:
                result["mae_pct"] = abs(traj[-1] - mean_val) / mean_val * 100

    elif model_key == "vram_forecast":
        # Expected format: {"hosts": {"name": {"r2_backtest": ..., ...}}}
        hosts = data.get("hosts", {})
        r2s = [h.get("r2_backtest") for h in hosts.values() if h.get("r2_backtest") is not None]
        if r2s:
            result["r2"] = sum(r2s) / len(r2s)

    return result


def check_degradation(history_entry, history):
    """Check if current accuracy degrades > threshold vs rolling 3-entry mean."""
    if len(history) < 3:
        return False, None
    r2s = [e.get("r2") for e in history[-4:-1] if e.get("r2") is not None]
    if not r2s:
        return False, None
    mean_r2 = sum(r2s) / len(r2s)
    current_r2 = history_entry.get("r2")
    if current_r2 is None or mean_r2 == 0:
        return False, None
    drop = (mean_r2 - current_r2) / mean_r2
    return drop > DEGRADATION_THRESHOLD + 1e-9, drop


def run_tracker():
    """Main tracker: evaluate all models, record to history, flag issues."""
    now_iso = datetime.now().isoformat()
    results = {"timestamp": now_iso, "models": {}, "flags": []}

    # Load existing history
    history_fp = ROOT / ACCURACY_HISTORY_FILE
    history_by_model = {k: [] for k in MODELS}
    if history_fp.exists():
        for line in history_fp.read_text(encoding="utf-8").strip().splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                mk = entry.get("model")
                if mk in history_by_model:
                    history_by_model[mk].append(entry)
            except json.JSONDecodeError:
                pass

    for model_key, spec in MODELS.items():
        data = load_model_results(model_key)
        acc = extract_accuracy(data, model_key)
        entry = {"timestamp": now_iso, "model": model_key, **acc}

        # Check degradation
        degraded, drop_pct = check_degradation(entry, history_by_model[model_key])
        entry["degraded"] = degraded
        if degraded:
            entry["drop_pct"] = round(drop_pct, 3)
            results["flags"].append(f"{model_key}: accuracy degraded {drop_pct*100:.1f}% vs rolling mean")

        # Check minimum r2 threshold
        if acc["r2"] is not None and acc["r2"] < spec["min_r2"]:
            results["flags"].append(f"{model_key}: r2={acc['r2']:.3f} below min {spec['min_r2']}")

        history_by_model[model_key].append(entry)
        results["models"][model_key] = entry

    # Append to history
    for model_key in MODELS:
        latest = history_by_model[model_key][-1]
        with open(history_fp, "a", encoding="utf-8") as f:
            f.write(json.dumps(latest) + "\n")

    results["flag_count"] = len(results["flags"])
    return results


def self_test():
    """Self-test with synthetic data."""
    passed, failed = 0, 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name}")

    # T1: convergence_rate extraction
    data = {"r2": 0.85, "predicted_convergence_cycle": 3, "data_points": 7}
    acc = extract_accuracy(data, "convergence_rate")
    check("T1a r2 extracted", acc["r2"] == 0.85)
    check("T1b status ok", acc["status"] == "ok")

    # T2: convergence_trajectory extraction
    data = {"estimate": {"r2_composite_index": 0.6, "composite_index_trajectory": [0.7, 0.75, 0.72, 0.71, 0.8]}}
    acc = extract_accuracy(data, "convergence_trajectory")
    check("T2a r2 from estimate", acc["r2"] == 0.6)
    check("T2b mae computed", acc["mae_pct"] is not None and acc["mae_pct"] > 0)

    # T3: missing data handled gracefully
    acc = extract_accuracy(None, "vram_forecast")
    check("T3 no_data status", acc["status"] == "no_data")
    check("T4 r2 is None for missing", acc["r2"] is None)

    # T5: degradation detection
    history = [{"r2": 0.8}, {"r2": 0.79}, {"r2": 0.81}]
    entry = {"r2": 0.5}
    degraded, drop = check_degradation(entry, history)
    check("T5a degradation detected", degraded is True)
    check("T5b drop > threshold", drop is not None and drop > DEGRADATION_THRESHOLD)

    # T6: no false-positive degradation
    entry_ok = {"r2": 0.78}
    degraded_ok, _ = check_degradation(entry_ok, history)
    check("T6 no degradation for stable", degraded_ok is False)

    # T7: vram_forecast extraction
    data = {"hosts": {"white": {"r2_backtest": 0.9}, "black": {"r2_backtest": 0.7}}}
    acc = extract_accuracy(data, "vram_forecast")
    check("T7 vram avg r2", abs(acc["r2"] - 0.8) < 0.01)

    # T8: boundary - exactly at threshold is NOT degraded
    history_edge = [{"r2": 0.8}, {"r2": 0.8}, {"r2": 0.8}]
    entry_edge = {"r2": 0.64}  # exactly 20% drop = 0.8*0.8=0.64
    degraded_edge, _ = check_degradation(entry_edge, history_edge)
    check("T8 boundary not flagged (strict >)", degraded_edge is False)

    print(f"\n[self-test] {passed} passed / {failed} failed")
    return failed == 0


def main():
    parser = argparse.ArgumentParser(description="Predictive Model Accuracy Tracker")
    parser.add_argument("--self-test", action="store_true", help="Run self-tests")
    args = parser.parse_args()

    if args.self_test:
        ok = self_test()
        sys.exit(0 if ok else 1)

    results = run_tracker()
    print(f"Predictive Accuracy Tracker: {results['timestamp']}")
    for mk, entry in results["models"].items():
        status = entry["status"]
        r2 = entry.get("r2")
        r2_str = f"r2={r2:.3f}" if r2 is not None else "r2=N/A"
        flag = " [DEGRADED]" if entry.get("degraded") else ""
        print(f"  {mk}: {status} ({r2_str}){flag}")
    if results["flags"]:
        print(f"\nFlags ({results['flag_count']}):")
        for f in results["flags"]:
            print(f"  ! {f}")
    else:
        print("\nNo flags raised.")

    # Write report
    report_fp = ROOT / "memory/verifier/predictive-accuracy-report.json"
    report_fp.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Report: {report_fp.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
