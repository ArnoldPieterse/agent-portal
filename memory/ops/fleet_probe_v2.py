#!/usr/bin/env python3
"""fleet_probe_v2.py - Adaptive trend-aware probe with predictive alerts.
Goal #3: if latency trending up >10% per interval over 3 consecutive probes, issue WARN before threshold hit.

Usage:
  python fleet_probe_v2.py              # run one probe cycle against DEFAULT_TARGETS
  python fleet_probe_v2.py --simulate   # simulate degrading host to verify predictive alert
  python fleet_probe_v2.py --test-predictive  # unit tests for predictive logic
"""
import os, json, time, statistics, sys
from datetime import datetime, timezone

HISTORY_FILE = "memory/ops/fleet-probe-history.jsonl"
HISTORY_WINDOW = 6
DRIFT_WARN_PCT = 50   # % above baseline median
DRIFT_CRIT_PCT = 200  # % above baseline median
PREDICTIVE_WARN_PCT = 10  # >10% increase per interval over 3 consecutive probes triggers predictive WARN

DEFAULT_TARGETS = [
    ("127.0.0.1", 8099),
]


def load_history():
    entries = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return entries


def save_entry(entry):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def probe_target(host, port, timeout=3.0):
    import socket
    start = time.monotonic()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        elapsed = (time.monotonic() - start) * 1000
        sock.close()
        return elapsed, None
    except (socket.timeout, ConnectionRefusedError, PermissionError, OSError) as e:
        return None, str(type(e).__name__)


def compute_baseline(history, host, port):
    relevant = [
        h["latency_ms"] for h in history
        if h.get("host") == host and h.get("port") == port and h.get("latency_ms") is not None
    ]
    recent = relevant[-HISTORY_WINDOW:]
    if len(recent) < 2:
        return None
    return statistics.median(recent)


def predictive_alert(history, host, port):
    """Check if latency trending up >10% per interval over 3 consecutive probes."""
    relevant = [
        h["latency_ms"] for h in history
        if h.get("host") == host and h.get("port") == port and h.get("latency_ms") is not None
    ]
    if len(relevant) < 4:
        return False, ""
    last4 = relevant[-4:]
    increases = []
    for i in range(1, len(last4)):
        prev, curr = last4[i-1], last4[i]
        if prev == 0:
            return False, ""
        increases.append((curr - prev) / prev * 100)
    if all(z > PREDICTIVE_WARN_PCT for z in increases):
        total_growth = (last4[-1] - last4[0]) / last4[0] * 100
        msg = f"latency trending up {total_growth:.0f}% over 3 intervals ({last4[0]:.1f}ms -> {last4[-1]:.1f}ms)"
        return True, msg
    return False, ""


def classify(latency_ms, baseline):
    if latency_ms is None:
        return "CRIT"
    if baseline is None or baseline == 0:
        return "OK"
    drift_pct = (latency_ms - baseline) / baseline * 100
    if drift_pct > DRIFT_CRIT_PCT:
        return "CRIT"
    elif drift_pct > DRIFT_WARN_PCT:
        return "WARN"
    return "OK"


def run_probe(targets=None):
    if targets is None:
        targets = DEFAULT_TARGETS
    history = load_history()
    results = []
    for host, port in targets:
        latency_ms, error = probe_target(host, port)
        baseline = compute_baseline(history, host, port)
        pred_alert, pred_msg = predictive_alert(history, host, port)
        severity = classify(latency_ms, baseline)
        if pred_alert and severity == "OK":
            severity = "WARN"
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "host": host, "port": port,
            "latency_ms": latency_ms, "error": error,
            "baseline_ms": baseline, "severity": severity,
            "predictive_alert": pred_alert,
        }
        save_entry(entry)
        results.append(entry)
        status_str = f"{host}:{port} -> {severity}"
        if latency_ms is not None:
            status_str += f" ({latency_ms:.1f}ms)"
        else:
            status_str += f" (ERROR: {error})"
        if pred_alert:
            status_str += f" [PREDICTIVE: {pred_msg}]"
        print(status_str)
    return results


def simulate_degradation():
    """Test: simulate degrading host, verify predictive alert fires before CRIT."""
    print("=== PREDICTIVE ALERT SIMULATION ===")
    base_latency = 100.0
    growth_rate = 0.15
    sim_entries = []
    for i in range(6):
        latency = base_latency * ((1 + growth_rate) ** i)
        sim_entries.append({"host": "simhost", "port": 9999, "latency_ms": round(latency, 2)})

    print(f"Simulated latencies: {[e['latency_ms'] for e in sim_entries]}")
    print(f"Growth rate: {growth_rate*100:.0f}% per interval\n")

    for check_idx in range(3, len(sim_entries)):
        history_so_far = sim_entries[:check_idx]
        pred, msg = predictive_alert(history_so_far, "simhost", 9999)
        if pred:
            current_latency = sim_entries[check_idx]["latency_ms"]
            drift_pct = (current_latency - base_latency) / base_latency * 100
            normal_sev = classify(current_latency, base_latency)
            print(f"PASS: Predictive WARN fires at probe {check_idx+1}")
            print(f"      {msg}")
            print(f"      Normal classification would be: {normal_sev} (drift={drift_pct:.0f}%)")
            assert normal_sev in ("OK", "WARN")
            print("\nRESULT: PASS - predictive alert fires before CRIT threshold")
            return True
    print("FAIL: Predictive WARN did not fire within simulated window")
    return False


if __name__ == "__main__":
    if "--simulate" in sys.argv:
        ok = simulate_degradation()
        sys.exit(0 if ok else 1)
    elif "--test-predictive" in sys.argv:
        print("=== UNIT TESTS: predictive_alert ===")
        steady = [{"host": "h", "port": 1, "latency_ms": v} for v in [100, 102, 98, 101]]
        growing = [{"host": "h", "port": 1, "latency_ms": v} for v in [100, 115, 132, 152]]
        partial = [{"host": "h", "port": 1, "latency_ms": v} for v in [100, 100, 115, 132]]
        exact = [{"host": "h", "port": 1, "latency_ms": v} for v in [100, 110, 121, 133.1]]
        just_over = [{"host": "h", "port": 1, "latency_ms": v} for v in [100, 110.5, 122.1, 134.9]]

        t1 = not predictive_alert(steady, "h", 1)[0]
        t2 = predictive_alert(growing, "h", 1)[0]
        t3 = not predictive_alert(partial, "h", 1)[0]
        t4 = not predictive_alert(exact, "h", 1)[0]
        t5 = predictive_alert(just_over, "h", 1)[0]

        print(f"  steady (no alert):       {'PASS' if t1 else 'FAIL'}")
        print(f"  growing >10%/interval:   {'PASS' if t2 else 'FAIL'}")
        print(f"  partial (only 2 up):     {'PASS' if t3 else 'FAIL'}")
        print(f"  exact 10% (boundary):    {'PASS' if t4 else 'FAIL'}")
        print(f"  just over 10%:           {'PASS' if t5 else 'FAIL'}")
        all_pass = all([t1, t2, t3, t4, t5])
        print(f"\n{'ALL PASS' if all_pass else 'SOME FAILED'} ({sum([t1,t2,t3,t4,t5])}/5)")
        sys.exit(0 if all_pass else 1)
    else:
        run_probe()
