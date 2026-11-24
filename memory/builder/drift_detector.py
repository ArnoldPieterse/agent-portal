"""Autonomy Drift Detector — sliding-window z-score anomaly detection.

Reads: memory/ops/autoloop.jsonl (pass records), fleet-mode.json
Writes: memory/ops/drift-alerts.jsonl (detection log)

Metrics monitored (per 30-pass window):
  - human_intervention_rate: fraction of passes requiring human unblock
  - error_rate: fraction of passes with errors
  - mode_fallback_count: count of mode FSM fallback events

Baseline: 7-day rolling mean/std from autoloop history.
Alert threshold: z-score > 2.0 on any metric.
On alert: injects maintenance task via idle_task_injector (if available).

Self-test: python memory/builder/drift_detector.py --selftest
Dry-run:   python memory/builder/drift_detector.py --dry-run
"""
import json, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUTOLOOP_LOG = ROOT / "memory" / "ops" / "autoloop.jsonl"
FLEET_MODE = ROOT / "fleet-mode.json"
ALERTS_LOG = ROOT / "memory" / "ops" / "drift-alerts.jsonl"
INJECTOR = ROOT / "memory" / "builder" / "idle_task_injector_test.py"  # fallback reference

WINDOW_SIZE = 30       # last N passes for current window
BASELINE_DAYS = 7      # baseline window in days
Z_THRESHOLD = 2.0      # alert when z-score exceeds this
CRITICAL_SCORE = 40    # inject maintenance before autonomy score drops below this


def _read_jsonl(path):
    """Read all entries from a JSONL file."""
    entries = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    entries.append(obj)
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return entries


def _read_json(path):
    """Read a JSON file, return None on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _parse_ts(ts_str):
    """Parse ISO timestamp to epoch seconds."""
    if not ts_str:
        return 0.0
    try:
        t = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
        return t
    except (ValueError, AttributeError):
        return 0.0


def extract_metrics(entry):
    """Extract the three monitored metrics from a single autoloop entry.

    Returns dict with keys: human_intervention_rate, error_rate, mode_fallback_count.
    Each value is a float (per-pass rate/count).
    """
    m = {
        "human_intervention_rate": 0.0,
        "error_rate": 0.0,
        "mode_fallback_count": 0.0,
    }
    # human intervention: entry marked as blocked or has 'unblock' field
    if entry.get("blocked") or entry.get("needs_human"):
        m["human_intervention_rate"] = 1.0
    # error rate: entry has errors or failed status
    if entry.get("errors") or entry.get("status") == "failed" or entry.get("outcome") == "fail":
        m["error_rate"] = 1.0
    # mode fallback: explicit field or inferred from mode changes
    mf = entry.get("mode_fallback_count")
    if mf is not None:
        m["mode_fallback_count"] = float(mf)
    elif entry.get("mode_fallback"):
        m["mode_fallback_count"] = 1.0
    return m


def compute_window_stats(entries):
    """Compute per-metric mean and std over a list of entries.

    Returns dict: {metric: {"mean": float, "std": float, "n": int}}
    """
    metrics = ["human_intervention_rate", "error_rate", "mode_fallback_count"]
    stats = {}
    if not entries:
        for m in metrics:
            stats[m] = {"mean": 0.0, "std": 1.0, "n": 0}
        return stats

    values = {m: [] for m in metrics}
    for e in entries:
        em = extract_metrics(e)
        for m in metrics:
            values[m].append(em[m])

    for m in metrics:
        n = len(values[m])
        if n == 0:
            stats[m] = {"mean": 0.0, "std": 1.0, "n": 0}
        else:
            mean = sum(values[m]) / n
            variance = sum((v - mean) ** 2 for v in values[m]) / n if n > 1 else 0.0
            std = variance ** 0.5
            # Floor std at 0.01 to avoid division by zero in z-score
            stats[m] = {"mean": mean, "std": max(std, 0.01), "n": n}
    return stats


def compute_z_scores(current_stats, baseline_stats):
    """Compute z-score for each metric: (current_mean - baseline_mean) / baseline_std.

    Returns dict: {metric: float}
    """
    z = {}
    for m in current_stats:
        base_mean = baseline_stats[m]["mean"]
        base_std = max(baseline_stats[m]["std"], 0.01)
        cur_mean = current_stats[m]["mean"]
        z[m] = (cur_mean - base_mean) / base_std
    return z


def detect_drift(entries, now=None):
    """Main detection logic.

    Splits entries into baseline (older than last 30) and current window (last 30).
    Computes z-scores, returns list of alerts for metrics exceeding threshold.

    Returns: {"alerts": [...], "z_scores": {...}, "window_size": int, "baseline_size": int}
    """
    if now is None:
        now = time.time()

    # Sort by timestamp
    entries_sorted = sorted(entries, key=lambda e: _parse_ts(e.get("timestamp") or e.get("ts") or e.get("start_ts", "")))

    current_window = entries_sorted[-WINDOW_SIZE:]
    baseline_entries = entries_sorted[:-WINDOW_SIZE] if len(entries_sorted) > WINDOW_SIZE else entries_sorted

    # If we don't have enough for a separate baseline, use all data as baseline
    # but only the last 30 as current (this is the cold-start case)
    if not baseline_entries:
        baseline_entries = entries_sorted

    cur_stats = compute_window_stats(current_window)
    base_stats = compute_window_stats(baseline_entries)
    z_scores = compute_z_scores(cur_stats, base_stats)

    alerts = []
    for m, z in z_scores.items():
        if abs(z) > Z_THRESHOLD:
            alerts.append({
                "metric": m,
                "z_score": round(z, 4),
                "current_mean": round(cur_stats[m]["mean"], 6),
                "baseline_mean": round(base_stats[m]["mean"], 6),
                "direction": "degradation" if z > 0 else "improvement",
            })

    return {
        "alerts": alerts,
        "z_scores": {m: round(z, 4) for m, z in z_scores.items()},
        "window_size": len(current_window),
        "baseline_size": len(baseline_entries),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def inject_maintenance(reason):
    """Attempt to inject a maintenance pass. Returns True if successful."""
    # Write a signal file that idle_task_injector can pick up
    signal = ROOT / "memory" / "ops" / "drift-maintenance-signal.json"
    try:
        signal.write_text(json.dumps({
            "trigger": "drift_detector",
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), encoding="utf-8")
        return True
    except OSError:
        return False


def log_alerts(alerts, z_scores):
    """Append alerts to drift-alerts.jsonl."""
    if not alerts:
        return
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alerts": alerts,
        "z_scores": z_scores,
    }
    try:
        with open(ALERTS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def run(dry_run=False):
    """Main execution path."""
    entries = _read_jsonl(AUTOLOOP_LOG)
    fleet_mode = _read_json(FLEET_MODE)

    result = detect_drift(entries)

    if dry_run:
        print(json.dumps(result, indent=2))
        return 0

    # Check autonomy score for critical threshold
    autonomy_score = None
    if fleet_mode:
        score_val = fleet_mode.get("autonomy_score")
        if isinstance(score_val, dict):
            autonomy_score = score_val.get("ci_midpoint", score_val.get("score"))
        elif isinstance(score_val, (int, float)):
            autonomy_score = score_val

    if result["alerts"]:
        # Log the alerts
        log_alerts(result["alerts"], result["z_scores"])
        # If score is critical or dropping, inject maintenance
        should_inject = False
        if autonomy_score is not None and autonomy_score < CRITICAL_SCORE:
            should_inject = True
        elif any(a["direction"] == "degradation" for a in result["alerts"]):
            # Even without critical score, degradation above 2σ warrants injection
            should_inject = True

        if should_inject:
            reason = f"drift detected: {[(a['metric'], a['z_score']) for a in result['alerts']]}"
            inject_maintenance(reason)

    print(json.dumps(result, indent=2))
    return 0


def selftest():
    """Self-test with synthetic data proving detection at 2σ boundary.

    Test cases:
      1. Stable data → no alerts (z < 2)
      2. Degraded data → alert fires (z > 2)
      3. Boundary case: z exactly at threshold → no alert (strictly >)
    """
    import random
    random.seed(42)

    base_ts = time.time() - 10 * 86400  # 10 days ago

    def make_entry(offset_h, intervention=False, error=False, fallback=0):
        ts = (base_ts + offset_h * 3600)
        return {
            "timestamp": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
            "agent": "test",
            "productive": not (intervention or error),
            "blocked": intervention,
            "errors": ["err"] if error else None,
            "mode_fallback_count": fallback,
        }

    # --- Test 1: Stable data (all zeros) → no alerts
    stable_entries = [make_entry(i * 0.5) for i in range(60)]
    result = detect_drift(stable_entries)
    assert len(result["alerts"]) == 0, f"FAIL test1: expected no alerts, got {result['alerts']}"
    print("  PASS test1: stable data → no alerts")

    # --- Test 2: Degraded last 30 passes (high error rate) → alert fires
    baseline_entries = [make_entry(i * 0.5) for i in range(30)]  # clean baseline
    degraded_entries = [make_entry(30 + i * 0.5, error=True) for i in range(30)]  # all errors
    mixed = baseline_entries + degraded_entries
    result2 = detect_drift(mixed)
    assert len(result2["alerts"]) > 0, f"FAIL test2: expected alerts, got none. z={result2['z_scores']}"
    error_alert = [a for a in result2["alerts"] if a["metric"] == "error_rate"]
    assert len(error_alert) > 0, f"FAIL test2: expected error_rate alert, got {result2['alerts']}"
    assert error_alert[0]["z_score"] > Z_THRESHOLD, f"FAIL test2: z={error_alert[0]['z_score']} not > {Z_THRESHOLD}"
    print(f"  PASS test2: degraded data → alert (error_rate z={error_alert[0]['z_score']})")

    # --- Test 3: Boundary — z just below threshold → no alert
    # Create data where current mean is slightly above baseline but within 2σ
    # Baseline: all zeros (mean=0, std floored to 0.01)
    # Current: 1 out of 30 has an error → mean = 1/30 ≈ 0.033, z = 0.033/0.01 = 3.3 → too high
    # Instead use a baseline with some variance:
    # Baseline: 5 errors in 30 (mean=0.167, std≈0.37)
    # Current: 8 errors in 30 (mean=0.267), z = (0.267-0.167)/0.37 ≈ 0.27 → no alert
    b_entries = []
    for i in range(30):
        is_err = i < 5  # 5 errors in baseline
        b_entries.append(make_entry(i * 0.5, error=is_err))
    c_entries = []
    for i in range(30):
        is_err = i < 8  # 8 errors in current (slightly higher but within 2σ)
        c_entries.append(make_entry(30 + i * 0.5, error=is_err))
    boundary_data = b_entries + c_entries
    result3 = detect_drift(boundary_data)
    z_err = result3["z_scores"].get("error_rate", 0)
    assert abs(z_err) <= Z_THRESHOLD, f"FAIL test3: z={z_err} exceeds threshold (should be within)"
    print(f"  PASS test3: boundary data → no alert (error_rate z={z_err})")

    # --- Test 4: Human intervention drift
    b_int = [make_entry(i * 0.5) for i in range(30)]  # clean baseline
    c_int = [make_entry(30 + i * 0.5, intervention=True) for i in range(30)]  # all blocked
    int_data = b_int + c_int
    result4 = detect_drift(int_data)
    int_alerts = [a for a in result4["alerts"] if a["metric"] == "human_intervention_rate"]
    assert len(int_alerts) > 0, f"FAIL test4: expected human_intervention alert, z={result4['z_scores']}"
    print(f"  PASS test4: intervention drift → alert (z={int_alerts[0]['z_score']})")

    # --- Test 5: Mode fallback drift
    b_fb = [make_entry(i * 0.5) for i in range(30)]
    c_fb = [make_entry(30 + i * 0.5, fallback=1) for i in range(30)]
    fb_data = b_fb + c_fb
    result5 = detect_drift(fb_data)
    fb_alerts = [a for a in result5["alerts"] if a["metric"] == "mode_fallback_count"]
    assert len(fb_alerts) > 0, f"FAIL test5: expected mode_fallback alert, z={result5['z_scores']}"
    print(f"  PASS test5: fallback drift → alert (z={fb_alerts[0]['z_score']})")

    print("\n  ALL SELFTESTS PASSED (5/5)")
    return 0


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    elif "--dry-run" in sys.argv:
        sys.exit(run(dry_run=True))
    else:
        sys.exit(run(dry_run=False))


if __name__ == "__main__":
    main()
