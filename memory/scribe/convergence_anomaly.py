"""Convergence Anomaly Detector - Scribe goal #8
Compares current cycle metrics against 3-cycle rolling average; flags >20% deviation.
Output: appends alerts to memory/ops/anomalies.jsonl
"""
import json, pathlib, sys
from datetime import datetime

try:
    ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # project root
except NameError:
    ROOT = pathlib.Path.cwd()
ANOMALY_FILE = ROOT / "memory" / "ops" / "anomalies.jsonl"
THRESHOLD = 0.20  # 20% deviation triggers alert

def load_metrics():
    """Load per-cycle metrics from available sources."""
    metrics = []
    
    # Autonomy score trend
    trend_file = ROOT / "memory" / "scribe" / "autonomy-trend.jsonl"
    if trend_file.exists():
        for line in trend_file.read_text(encoding="utf-8").strip().split("\n"):
            if line.strip():
                e = json.loads(line)
                metrics.append({
                    "cycle": e.get("cycle"),
                    "autonomy_score": e.get("score"),
                    "ts": e.get("ts", ""),
                })
    
    # Intervention counts (from patterns file)
    patterns_file = ROOT / "memory" / "scribe" / "intervention-patterns.jsonl"
    if patterns_file.exists():
        cycle_counts = {}
        for line in patterns_file.read_text(encoding="utf-8").strip().split("\n"):
            if line.strip():
                e = json.loads(line)
                c = e.get("cycle", 0)
                cycle_counts[c] = cycle_counts.get(c, 0) + 1
        for m in metrics:
            m["intervention_count"] = cycle_counts.get(m.get("cycle"), 0)
    
    # Cycle durations (from ops if available)
    dur_file = ROOT / "memory" / "ops" / "cycle-durations.jsonl"
    if dur_file.exists():
        for line in dur_file.read_text(encoding="utf-8").strip().split("\n"):
            if line.strip():
                e = json.loads(line)
                c = e.get("cycle")
                for m in metrics:
                    if m.get("cycle") == c:
                        m["cycle_duration_h"] = e.get("duration_hours", e.get("duration_h"))
    
    return [m for m in metrics if m.get("cycle")]

def rolling_avg(values, window=3):
    """Compute rolling average over last `window` values (excluding current)."""
    if len(values) < 2:
        return None
    prev = values[-(window+1):-1] if len(values) > 1 else []
    if not prev:
        return None
    return sum(prev) / len(prev)

def detect_anomalies(metrics):
    """Compare each metric against rolling average; flag >20% deviation."""
    alerts = []
    
    for key in ["autonomy_score", "intervention_count", "cycle_duration_h"]:
        values = [m.get(key) for m in metrics if m.get(key) is not None]
        if len(values) < 2:
            continue
        
        current = values[-1]
        avg = rolling_avg(values, window=3)
        if avg is None or avg == 0:
            continue
        
        deviation = (current - avg) / abs(avg)
        if abs(deviation) > THRESHOLD:
            alerts.append({
                "metric": key,
                "current": current,
                "rolling_avg_3": round(avg, 2),
                "deviation_pct": round(deviation * 100, 1),
                "direction": "spike" if deviation > 0 else "drop",
                "threshold_pct": THRESHOLD * 100,
            })
    
    return alerts

def main():
    metrics = load_metrics()
    if not metrics:
        print("No metrics found. Nothing to check.")
        return 0
    
    current_cycle = metrics[-1].get("cycle", "?")
    print(f"Checking cycle {current_cycle} against rolling 3-cycle average...")
    print(f"Metrics loaded: {len(metrics)} cycles")
    
    alerts = detect_anomalies(metrics)
    
    if alerts:
        for a in alerts:
            timestamp = datetime.now().isoformat()
            record = {
                "ts": timestamp,
                "cycle": current_cycle,
                "type": "convergence_anomaly",
                **a,
            }
            ANOMALY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(ANOMALY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            print(f"  ALERT: {a['metric']} {a['direction']} {a['deviation_pct']}% (avg={a['rolling_avg_3']}, current={a['current']})")
    else:
        print("  No anomalies detected (all metrics within ±20% of rolling average).")
    
    # Always write a status record for audit
    status = {
        "ts": datetime.now().isoformat(),
        "cycle": current_cycle,
        "type": "anomaly_check_run",
        "alerts_fired": len(alerts),
        "metrics_checked": [k for k in ["autonomy_score", "intervention_count", "cycle_duration_h"] 
                           if any(m.get(k) is not None for m in metrics)],
    }
    ANOMALY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ANOMALY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(status) + "\n")
    
    print(f"  Status recorded to {ANOMALY_FILE.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
