#!/usr/bin/env python3
"""fleet_probe_v2_predictive_test.py - Predictive alert simulation (Mechanic goal #3).

Acceptance: simulate a degrading host -> WARN fires one interval before CRIT would have.
Implements linear-trend prediction: if latency is trending up >10% per interval
over 3 consecutive probes, issue a PREDICTIVE_WARN before the threshold is hit.

No network - fully sandbox-safe. Writes evidence to
memory/mechanic/fleet_probe_v2_predictive_evidence.jsonl.
Run: python memory/mechanic/fleet_probe_v2_predictive_test.py
"""
import json, os, sys
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Core predictive logic (would be integrated into fleet_probe_v2.py in prod)
# ---------------------------------------------------------------------------

PREDICTIVE_WINDOW = 3       # minimum consecutive intervals to detect trend
PREDICTIVE_THRESHOLD_PCT = 10.0  # >10% rise per interval triggers WARN
CRIT_LATENCY_MS = 500.0     # threshold at which latency is CRIT
WARN_LATENCY_MS = 200.0     # threshold at which latency is WARN

def linear_slope(values: List[float]) -> float:
    """Simple least-squares slope of values indexed 0..n-1."""
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den != 0 else 0.0

def pct_per_interval(values: List[float]) -> float:
    """Average percentage rise per interval (slope / mean * 100)."""
    if len(values) < 2:
        return 0.0
    slope = linear_slope(values)
    y_mean = sum(values) / len(values)
    if y_mean == 0:
        return 0.0
    return (slope / y_mean) * 100.0

def predict_next(values: List[float]) -> float:
    """Predict next value using linear extrapolation."""
    if len(values) < 2:
        return values[-1] if values else 0.0
    slope = linear_slope(values)
    return values[-1] + slope

def classify_latency(latency_ms: float) -> str:
    """Standard classification (mirrors fleet_probe_v2)."""
    if latency_ms >= CRIT_LATENCY_MS:
        return "CRIT"
    if latency_ms >= WARN_LATENCY_MS:
        return "WARN"
    return "OK"

def predictive_alert(history: List[float]) -> Optional[str]:
    """Return 'PREDICTIVE_WARN' if trend is rising >10%/interval for 3+ consecutive
    intervals, OR if predicted next value would cross WARN threshold. None otherwise."""
    if len(history) < PREDICTIVE_WINDOW:
        return None
    # Check slope over last N points
    recent = history[-PREDICTIVE_WINDOW:]
    pct = pct_per_interval(recent)
    if pct > PREDICTIVE_THRESHOLD_PCT:
        return "PREDICTIVE_WARN"
    # Also check if predicted next value crosses WARN even if current is OK
    pred = predict_next(history)
    if pred >= WARN_LATENCY_MS and history[-1] < WARN_LATENCY_MS:
        return "PREDICTIVE_WARN"
    return None

# ---------------------------------------------------------------------------
# Simulation: degrading host with latency rising ~25%/interval
# ---------------------------------------------------------------------------

def run_sim():
    # Latency sequence: starts at 80ms, grows by ~25% each interval.
    # Standard thresholds: WARN at 200ms, CRIT at 500ms.
    # Without prediction: first WARN at run 4 (156.25 -> 195.3 still OK; 244 > 200)
    # With prediction: should fire PREDICTIVE_WARN at run 3 (before threshold hit)
    latencies = [80.0, 100.0, 125.0, 156.25, 195.3, 244.1, 305.2, 381.5,
                 476.9, 596.1]  # 10 runs
    rows = []
    history: List[float] = []
    for i, lat in enumerate(latencies):
        std_sev = classify_latency(lat)
        pred_alert = predictive_alert(history)  # uses prior points only
        effective_sev = "PREDICTIVE_WARN" if pred_alert else std_sev
        rows.append({
            "run": i + 1,
            "latency_ms": round(lat, 2),
            "standard_severity": std_sev,
            "predictive_alert": pred_alert,
            "effective_severity": effective_sev,
            "history_len": len(history),
        })
        history.append(lat)
    return rows

def main():
    rows = run_sim()
    print(f"{'run':>3} {'lat_ms':>8} {'std_sev':>10} {'pred_alert':>14} {'eff_sev':>16}")
    for r in rows:
        pa = r["predictive_alert"] or "-"
        print(f"{r['run']:>3} {r['latency_ms']:>8.2f} {r['standard_severity']:>10} "
              f"{pa:>14} {r['effective_severity']:>16}")

    # Acceptance: PREDICTIVE_WARN fires at least one interval BEFORE first standard WARN/CRIT
    first_std_warn_run = None
    for r in rows:
        if r["standard_severity"] in ("WARN", "CRIT"):
            first_std_warn_run = r["run"]
            break
    first_pred_run = None
    for r in rows:
        if r["predictive_alert"] == "PREDICTIVE_WARN":
            first_pred_run = r["run"]
            break

    ok = (first_pred_run is not None and
          first_std_warn_run is not None and
          first_pred_run < first_std_warn_run)

    print(f"\nFirst standard WARN/CRIT: run {first_std_warn_run}")
    print(f"First PREDICTIVE_WARN:     run {first_pred_run}")
    print(f"Predictive fired before standard: {ok}")
    print(f"PASS: {ok}")

    # Write evidence
    evidence_path = os.path.join(os.path.dirname(__file__),
                                 "fleet_probe_v2_predictive_evidence.jsonl")
    with open(evidence_path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(f"evidence -> {os.path.relpath(evidence_path)}")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
