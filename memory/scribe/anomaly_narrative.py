#!/usr/bin/env python3
"""Anomaly Narrative Generator (Scribe goal #8, cycle 15).

When any fleet metric deviates >2 sigma from 30-day baseline, generate a
plain-English explanation: what deviated, by how much, likely cause, recommended action.

Usage: python memory/scribe/anomaly_narrative.py [--test]
Output: memory/ops/anomaly-{timestamp}.md
"""
import json, sys, statistics
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
OPS_DIR = BASE / "memory" / "ops"
DECISION_LOG = OPS_DIR / "decision-log.jsonl"


def compute_baseline(values: list[float]) -> tuple[float, float]:
    """Return (mean, std) of a value series."""
    if len(values) < 2:
        return sum(values) / max(len(values), 1), 0.0
    return statistics.mean(values), statistics.stdev(values)


def detect_anomalies(metric_name: str, baseline: list[float], current: float) -> dict | None:
    """Check if current value deviates >2 sigma from baseline."""
    mean, std = compute_baseline(baseline)
    if std == 0:
        return None
    z_score = (current - mean) / std
    if abs(z_score) > 2:
        return {
            "metric": metric_name,
            "current": current,
            "baseline_mean": round(mean, 2),
            "baseline_std": round(std, 2),
            "z_score": round(z_score, 2),
            "direction": "above" if z_score > 0 else "below",
        }
    return None


def find_likely_cause(anomaly: dict) -> str:
    """Search decision-log for context around the anomaly."""
    if not DECISION_LOG.exists():
        return "No decision-log entries found to ground cause analysis."
    lines = []
    try:
        for line in DECISION_LOG.read_text(encoding="utf-8").strip().split("\n"):
            if line.strip():
                try:
                    d = json.loads(line)
                    text = json.dumps(d).lower()
                    if anomaly["metric"].split("_")[0].lower()[:4] in text:
                        lines.append(d.get("decision", d.get("text", line[:80])))
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    if lines:
        return f"Decision-log context: {lines[-1][:100]}"
    return "No specific cause identified in logs; likely a systemic shift."


def recommend_action(anomaly: dict) -> str:
    """Generate an actionable recommendation."""
    direction = anomaly["direction"]
    metric = anomaly["metric"]
    if "productivity" in metric or "productive" in metric:
        if direction == "below":
            return "Review agent dispatch quality; check if idle tasks are too generic. Consider tightening the rotation table."
        else:
            return "Productivity spike detected - verify it is sustainable and not a measurement artifact before adjusting baselines."
    elif "pass" in metric or "budget" in metric:
        if direction == "above":
            return "Pass consumption is elevated. Check for loop conditions or redundant verification cycles in the auto-loop."
        else:
            return "Pass usage dropped - verify agents are still being dispatched correctly and not silently failing."
    elif "goal" in metric:
        if direction == "below":
            return "Goal completion rate is below baseline. Check for blockers or misrouted goals; review seat availability."
        else:
            return "Goal completion spike - verify evidence quality to ensure closures are genuine."
    return f"Investigate {metric} deviation ({direction} baseline). Check recent fleet changes and agent health."


def generate_narrative(anomaly: dict) -> str:
    """Generate plain-English anomaly narrative."""
    cause = find_likely_cause(anomaly)
    action = recommend_action(anomaly)
    return (
        f"**Metric:** {anomaly['metric']}\n"
        f"**Deviation:** {anomaly['current']} (baseline mean: {anomaly['baseline_mean']}, "
        f"std: {anomaly['baseline_std']}, z-score: {anomaly['z_score']}) - {anomaly['direction']} baseline by >2 sigma.\n"
        f"**Likely cause:** {cause}\n"
        f"**Recommended action:** {action}"
    )


def main():
    test_mode = "--test" in sys.argv

    if test_mode:
        # Synthetic: 30-day baseline of productivity rates, one anomalous point
        import random
        random.seed(42)
        baseline = [80 + random.gauss(0, 3) for _ in range(30)]  # mean~80, std~3
        current = 65.0  # well below 2 sigma (z ~ -5)

        anomaly = detect_anomalies("productive_pass_rate", baseline, current)
        assert anomaly is not None, "Test failed: expected anomaly not detected"
        assert anomaly["direction"] == "below", f"Expected 'below', got {anomaly['direction']}"
        assert abs(anomaly["z_score"]) > 2, f"z-score {anomaly['z_score']} should be >2"

        narrative = generate_narrative(anomaly)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = OPS_DIR / f"anomaly-{ts}.md"
        OPS_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_text(f"# Anomaly Report - {ts}\n\n{narrative}\n", encoding="utf-8")

        # Verify
        content = out_path.read_text(encoding="utf-8")
        assert "productive_pass_rate" in content, "Metric name missing"
        assert "below" in content.lower(), "Direction missing"
        assert "Recommended action:" in content, "Action missing"
        print(f"Wrote: {out_path.relative_to(BASE)}")
        print(f"  Metric: {anomaly['metric']}")
        print(f"  Direction: {anomaly['direction']}, z={anomaly['z_score']}")
        print("  VERIFICATION PASSED")
    else:
        # Production: check real metrics
        print("No anomaly detection triggered (no live metric feed connected yet).")


if __name__ == "__main__":
    main()
