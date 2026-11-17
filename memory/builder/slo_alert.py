"""SLO alerting layer (Builder goal #2, cycle-3).

Checks p95 > 2000ms or p99 > 5000ms per endpoint over a rolling 10-min window.
On breach: writes HOTLINE one-liner to memory/ops/slo-alerts.jsonl + returns flag
for /api/health inclusion.

Usage (standalone test):
    python memory/builder/slo_alert.py --simulate
"""
import json, os, time, sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SLO_ALERT_LOG = os.path.join(HERE, "memory", "ops", "slo-alerts.jsonl")
WINDOW_S = 600          # 10-min rolling window
P95_THRESHOLD_MS = 2000 # 2 s
P99_THRESHOLD_MS = 5000 # 5 s


def _percentile(vals, pct):
    if not vals:
        return 0.0
    vs = sorted(vals)
    k = (len(vs) - 1) * pct / 100.0
    f = int(k)
    c = min(f + 1, len(vs) - 1)
    return round(vs[f] + (vs[c] - vs[f]) * (k - f), 2)


def check_slo(perf_records):
    """perf_records: list of (timestamp_float, path_str, ms_float).
    Returns dict with 'breached' bool, 'alerts' list, 'window_s'.
    Side-effect: appends HOTLINE line(s) to SLO_ALERT_LOG on breach."""
    now = time.time()
    cutoff = now - WINDOW_S
    per = {}
    for ts, path, ms in perf_records:
        if ts >= cutoff:
            per.setdefault(path, []).append(ms)

    alerts = []
    for path, vals in sorted(per.items()):
        p95 = _percentile(vals, 95)
        p99 = _percentile(vals, 99)
        if p95 > P95_THRESHOLD_MS or p99 > P99_THRESHOLD_MS:
            alerts.append({"path": path, "p95_ms": p95, "p99_ms": p99,
                           "n": len(vals), "window_s": WINDOW_S})

    if alerts:
        _write_hotline(alerts)

    return {"breached": bool(alerts), "alerts": alerts, "window_s": WINDOW_S}


def _write_hotline(alerts):
    """Append one HOTLINE line per breached endpoint to slo-alerts.jsonl."""
    os.makedirs(os.path.dirname(SLO_ALERT_LOG), exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for a in alerts:
        line = (f"H-SLO | portal | {a['path']} p95={a['p95_ms']}ms p99={a['p99_ms']}ms "
                f"(n={a['n']}, window={a['window_s']}s) exceeds budget "
                f"(p95<{P95_THRESHOLD_MS}ms, p99<{P99_THRESHOLD_MS}ms) | Builder | ack-by {ts}\n")
        with open(SLO_ALERT_LOG, "a", encoding="utf-8") as f:
            f.write(line)


def get_slo_status():
    """Read the last N alerts from SLO_ALERT_LOG for /api/health inclusion."""
    if not os.path.isfile(SLO_ALERT_LOG):
        return {"slo_breached": False, "last_alerts": []}
    lines = []
    try:
        with open(SLO_ALERT_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    lines.append(line)
    except OSError:
        pass
    last = lines[-5:] if lines else []
    return {"slo_breached": bool(last), "last_alerts": last}


# --- Standalone test mode ---
if __name__ == "__main__":
    if "--simulate" in sys.argv:
        now = time.time()
        # Simulate: /api/slow endpoint with p95 ~3000ms, p99 ~7000ms
        records = [(now - i * 2, "/api/slow", 2500 + (i % 5) * 800) for i in range(60)]
        # Normal endpoint: all fast
        records += [(now - i * 2, "/api/fast", 50 + (i % 3) * 10) for i in range(60)]
        result = check_slo(records)
        print(json.dumps(result, indent=2))
        status = get_slo_status()
        print("\n/api/health inclusion:")
        print(json.dumps(status, indent=2))
    else:
        print(__doc__)
