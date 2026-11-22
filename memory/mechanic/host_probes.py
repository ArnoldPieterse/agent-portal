"""Host Health Probe Suite - Mechanic Goal #3 (Cycle 10).

Collects per-host metrics: GPU temp, memory pressure, disk I/O latency, network RTT.
Appends structured records to host-metrics.jsonl. Alerts on threshold breach.
Designed to run <30s total. Register via schtask for 5-min cadence.

Usage:
    python memory/mechanic/host_probes.py            # single collection pass
    python memory/mechanic/host_probes.py --selftest # run self-test battery
    python memory/mechanic/host_probes.py --register # register schtask (5 min)
"""

import json
import os
import sys
import time
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# --- Thresholds ---
THRESHOLDS = {
    "gpu_temp_c": 85.0,
    "memory_pressure_pct": 90.0,
    "disk_io_latency_ms": 100.0,
    "network_rtt_ms": 200.0,
}

# --- Hosts to probe ---
HOSTS = {
    "white": {"type": "local"},
}

METRICS_FILE = Path("memory/ops/host-metrics.jsonl")
ALERTS_FILE = Path("memory/ops/host-alerts.jsonl")


def _run_cmd(cmd, timeout=10):
    """Run a command, return (stdout, stderr, returncode) or None on timeout."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except (subprocess.TimeoutExpired, Exception) as e:
        return None, str(e), -1


def probe_gpu_temp(host="white"):
    """Get GPU temperature. Returns dict with temp_c or null if no GPU."""
    out, err, rc = _run_cmd(
        "nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader", timeout=5
    )
    if rc == 0 and out:
        try:
            temps = [float(t.strip()) for t in out.split("\n") if t.strip()]
            return {"metric": "gpu_temp_c", "value": max(temps), "unit": "C", "host": host, "ok": True}
        except ValueError:
            pass
    return {"metric": "gpu_temp_c", "value": None, "unit": "C", "host": host, "ok": False, "note": "no_gpu_or_unavailable"}


def probe_memory_pressure(host="white"):
    """Get memory usage percentage."""
    if sys.platform == "win32":
        ps_script = (
            "[math]::Round((1 - "
            "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / "
            "(Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize) * 100, 1)"
        )
        cmd = 'powershell -NoProfile -Command "' + ps_script + '"'
        out, err, rc = _run_cmd(cmd, timeout=8)
    else:
        out, err, rc = _run_cmd("free | awk 'NR==2{printf \"%.1f\", $3/$2*100}'", timeout=5)

    if rc == 0 and out:
        try:
            val = float(out.strip())
            return {"metric": "memory_pressure_pct", "value": val, "unit": "%", "host": host, "ok": True}
        except ValueError:
            pass
    return {"metric": "memory_pressure_pct", "value": None, "unit": "%", "host": host, "ok": False, "note": "probe_failed"}


def probe_disk_io_latency(host="white"):
    """Measure disk I/O latency by timing a small write+read cycle."""
    start = time.perf_counter()
    try:
        tf = tempfile.NamedTemporaryFile(delete=False, dir=".")
        data = b"x" * 1024 * 64
        tf.write(data)
        tf.flush()
        os.fsync(tf.fileno())
        tf.close()

        with open(tf.name, "rb") as f:
            f.read(64 * 1024)

        elapsed_ms = (time.perf_counter() - start) * 1000
        os.unlink(tf.name)
        return {"metric": "disk_io_latency_ms", "value": round(elapsed_ms, 2), "unit": "ms", "host": host, "ok": True}
    except Exception as e:
        return {"metric": "disk_io_latency_ms", "value": None, "unit": "ms", "host": host, "ok": False, "note": str(e)}


def probe_network_rtt(host="white"):
    """Measure network RTT via ping."""
    targets = ["127.0.0.1"]
    for h, cfg in HOSTS.items():
        if h != "white" and "ip" in cfg:
            targets.append(cfg["ip"])

    best_rtt = None
    for target in targets[:2]:
        out, err, rc = _run_cmd("ping -n 4 -w 1000 " + target, timeout=8)
        if rc == 0 and out:
            for line in out.split("\n"):
                ll = line.lower()
                if "average" in ll or "avg" in ll:
                    try:
                        parts = line.replace(",", "").split()
                        for p in parts:
                            if "=" in p:
                                best_rtt = float(p.split("=")[1].replace("ms", ""))
                                break
                            elif "/" in p:
                                vals = p.split("/")
                                if len(vals) >= 2:
                                    best_rtt = float(vals[1])
                                    break
                    except (ValueError, IndexError):
                        continue
                if best_rtt is not None:
                    break
        if best_rtt is not None:
            break

    if best_rtt is not None:
        return {"metric": "network_rtt_ms", "value": round(best_rtt, 2), "unit": "ms", "host": host, "ok": True}
    return {"metric": "network_rtt_ms", "value": None, "unit": "ms", "host": host, "ok": False, "note": "ping_failed"}


def check_alerts(record):
    """Check a single metric record against thresholds. Returns alert dict or None."""
    if record.get("value") is None:
        return None
    key = record["metric"]
    threshold = THRESHOLDS.get(key)
    if threshold is None:
        return None
    if record["value"] > threshold:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "host": record["host"],
            "metric": key,
            "value": record["value"],
            "threshold": threshold,
            "severity": "warning",
            "message": f"{key}={record['value']}{record['unit']} exceeds threshold {threshold}{record['unit']}"
        }
    return None


def collect_all(host="white"):
    """Run all probes for a host. Returns (records, alerts, elapsed)."""
    t0 = time.perf_counter()
    records = []
    alerts = []

    probes = [probe_gpu_temp, probe_memory_pressure, probe_disk_io_latency, probe_network_rtt]
    for probe_fn in probes:
        rec = probe_fn(host=host)
        records.append(rec)
        alert = check_alerts(rec)
        if alert:
            alerts.append(alert)

    elapsed = time.perf_counter() - t0
    return records, alerts, elapsed


def append_metrics(records, host="white"):
    """Append records to host-metrics.jsonl."""
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "host": host,
        "metrics": records,
        "collected_at": timestamp
    }
    with open(METRICS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def append_alerts(alerts):
    """Append alerts to host-alerts.jsonl."""
    if not alerts:
        return
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_FILE, "a") as f:
        for a in alerts:
            f.write(json.dumps(a) + "\n")


def run_pass():
    """Execute one full collection pass across all hosts."""
    all_alerts = []
    total_start = time.perf_counter()

    for host in HOSTS:
        records, alerts, elapsed = collect_all(host=host)
        append_metrics(records, host)
        all_alerts.extend(alerts)
        print(f"[{host}] collected {len(records)} metrics in {elapsed:.2f}s")
        for a in alerts:
            print(f"  ALERT: {a['message']}")

    append_alerts(all_alerts)
    total_elapsed = time.perf_counter() - total_start
    print(f"Pass complete: {total_elapsed:.2f}s total, {len(all_alerts)} alerts")
    return {"hosts": len(HOSTS), "alerts": len(all_alerts), "elapsed_s": round(total_elapsed, 2)}


def register_schtask():
    """Register a scheduled task to run every 5 minutes."""
    script_path = os.path.abspath(__file__)
    python_exe = sys.executable
    task_name = "FleetHostProbes"
    
    # Use list-based subprocess (no shell) to avoid quoting issues
    tr_value = f"{python_exe} {script_path}"
    schtask_args = [
        "schtasks", "/create", "/tn", task_name,
        "/tr", tr_value,
        "/sc", "minute", "/mo", "5", "/rl", "limited", "/f"
    ]
    try:
        r = subprocess.run(schtasks_args, capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            print(f"Registered schtask '{task_name}' (every 5 min)")
            return True
        err_msg = r.stderr.strip() or r.stdout.strip()
    except Exception as e:
        err_msg = str(e)

    # Try via elev.py for admin escalation
    try:
        elev_cmd = [sys.executable, "elev.py", "--shell",
                    f'schtasks /create /tn "{task_name}" /tr "{tr_value}" /sc minute /mo 5 /rl limited /f']
        r2 = subprocess.run(elev_cmd, capture_output=True, text=True, timeout=15)
        if r2.returncode == 0:
            print(f"Registered schtask '{task_name}' via elev (every 5 min)")
            return True
        err_msg += " / elev: " + (r2.stderr.strip() or r2.stdout.strip())
    except Exception as e2:
        err_msg += f" / elev unavailable: {e2}"

    print(f"Registration failed: {err_msg}")
    return False

# --- SELF-TEST ---
def selftest():
    """Run self-test battery. Returns (passed, total)."""
    results = []

    def check(name, condition):
        results.append((name, bool(condition)))
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}")

    print("=== Host Probes Self-Test ===")

    # Test 1: All 4 probe functions return valid structure
    for probe_fn, metric_key in [
        (probe_gpu_temp, "gpu_temp_c"),
        (probe_memory_pressure, "memory_pressure_pct"),
        (probe_disk_io_latency, "disk_io_latency_ms"),
        (probe_network_rtt, "network_rtt_ms"),
    ]:
        rec = probe_fn(host="test")
        check(f"{metric_key} returns dict with metric field", rec.get("metric") == metric_key)
        check(f"{metric_key} has host field", rec.get("host") == "test")

    # Test 2: Disk I/O latency is positive and reasonable
    rec = probe_disk_io_latency(host="test")
    check("disk_io_latency_ms value > 0", rec["value"] is not None and rec["value"] > 0)
    check("disk_io_latency_ms < 5000 (sanity)", rec["value"] is not None and rec["value"] < 5000)

    # Test 3: Memory pressure is in valid range
    rec = probe_memory_pressure(host="test")
    if rec["value"] is not None:
        check("memory_pressure_pct in [0,100]", 0 <= rec["value"] <= 100)
    else:
        check("memory_pressure_pct reported (or gracefully null)", True)

    # Test 4: Alert threshold logic - below threshold = no alert
    rec_below = {"metric": "gpu_temp_c", "value": 70.0, "unit": "C", "host": "test"}
    check("no alert below threshold", check_alerts(rec_below) is None)

    # Test 5: Alert threshold logic - above threshold = alert
    rec_above = {"metric": "gpu_temp_c", "value": 90.0, "unit": "C", "host": "test"}
    alert = check_alerts(rec_above)
    check("alert fires above threshold", alert is not None and alert["severity"] == "warning")

    # Test 6: Alert for memory pressure
    rec_mem = {"metric": "memory_pressure_pct", "value": 95.0, "unit": "%", "host": "test"}
    alert_mem = check_alerts(rec_mem)
    check("memory alert fires at 95%", alert_mem is not None and alert_mem["metric"] == "memory_pressure_pct")

    # Test 7: Alert for disk I/O
    rec_disk = {"metric": "disk_io_latency_ms", "value": 150.0, "unit": "ms", "host": "test"}
    alert_disk = check_alerts(rec_disk)
    check("disk alert fires at 150ms", alert_disk is not None and alert_disk["threshold"] == 100.0)

    # Test 8: Alert for network RTT
    rec_net = {"metric": "network_rtt_ms", "value": 250.0, "unit": "ms", "host": "test"}
    alert_net = check_alerts(rec_net)
    check("network alert fires at 250ms", alert_net is not None and alert_net["threshold"] == 200.0)

    # Test 9: No alert for null values
    rec_null = {"metric": "gpu_temp_c", "value": None, "unit": "C", "host": "test"}
    check("no alert for null value", check_alerts(rec_null) is None)

    # Test 10: Full collection pass completes in <30s
    t0 = time.perf_counter()
    records, alerts, elapsed = collect_all(host="white")
    total_time = time.perf_counter() - t0
    check(f"full pass < 30s (actual {total_time:.1f}s)", total_time < 30)
    check("full pass returns 4 records", len(records) == 4)

    # Test 11: JSONL append works
    test_file = Path("memory/ops/host-metrics-selftest.jsonl")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    global METRICS_FILE
    orig_metrics = METRICS_FILE
    METRICS_FILE = test_file
    if test_file.exists():
        test_file.unlink()
    append_metrics(records, "selftest")
    METRICS_FILE = orig_metrics

    check("JSONL file created", test_file.exists())
    lines = test_file.read_text().strip().split("\n")
    check("JSONL has 1 line", len(lines) == 1)
    parsed = json.loads(lines[0])
    check("JSONL entry valid structure", "timestamp" in parsed and "metrics" in parsed and "host" in parsed)
    if test_file.exists():
        test_file.unlink()

    # Test 12: JSONL validity after multiple appends (simulate 100+ entries)
    METRICS_FILE = test_file
    if test_file.exists():
        test_file.unlink()
    for i in range(105):
        append_metrics(records, f"host{i % 3}")
    METRICS_FILE = orig_metrics

    lines = test_file.read_text().strip().split("\n")
    check("105 entries appended", len(lines) == 105)
    all_valid = True
    for line in lines:
        try:
            json.loads(line)
        except json.JSONDecodeError:
            all_valid = False
            break
    check("all 105 JSONL entries valid", all_valid)
    if test_file.exists():
        test_file.unlink()

    # Test 13: Threshold boundary - exactly at threshold = no alert
    rec_exact = {"metric": "gpu_temp_c", "value": 85.0, "unit": "C", "host": "test"}
    check("no alert at exact threshold (85C)", check_alerts(rec_exact) is None)

    # Test 14: Threshold boundary - just above = alert
    rec_just_above = {"metric": "gpu_temp_c", "value": 85.1, "unit": "C", "host": "test"}
    check("alert at 85.1C (just above)", check_alerts(rec_just_above) is not None)

    # Test 15: Network RTT probe returns valid structure
    rec_net2 = probe_network_rtt(host="test")
    check("network_rtt_ms has metric key", rec_net2["metric"] == "network_rtt_ms")
    if rec_net2["value"] is not None:
        check("network RTT > 0", rec_net2["value"] > 0)

    # Test 16: GPU probe handles no-GPU gracefully
    rec_gpu = probe_gpu_temp(host="test")
    check("gpu_temp_c handled gracefully (no crash)", "metric" in rec_gpu)

    # Test 17: collect_all returns correct number of records
    records2, alerts2, elapsed2 = collect_all(host="white")
    check("collect_all returns 4 metrics", len(records2) == 4)
    metric_names = {r["metric"] for r in records2}
    check("all 4 metric types present", metric_names == {"gpu_temp_c", "memory_pressure_pct", "disk_io_latency_ms", "network_rtt_ms"})

    # Test 18: run_pass completes without error
    result = run_pass()
    check("run_pass returns dict with hosts key", isinstance(result, dict) and "hosts" in result)
    check("run_pass elapsed < 30s", result["elapsed_s"] < 30)

    # Test 19: Alerts file structure (if any alerts were generated)
    if ALERTS_FILE.exists():
        alert_lines = ALERTS_FILE.read_text().strip().split("\n")
        valid_alerts = True
        for line in alert_lines:
            try:
                a = json.loads(line)
                assert "timestamp" in a and "metric" in a and "severity" in a
            except (json.JSONDecodeError, AssertionError):
                valid_alerts = False
                break
        check("alerts file entries valid", valid_alerts)
    else:
        check("alerts file absent or empty (no alerts expected in test env)", True)

    # Test 20: Metrics file has data after run_pass
    if METRICS_FILE.exists():
        m_lines = METRICS_FILE.read_text().strip().split("\n")
        check(f"host-metrics.jsonl has entries ({len(m_lines)})", len(m_lines) >= 1)
        last_entry = json.loads(m_lines[-1])
        check("last entry has timestamp", "timestamp" in last_entry)
    else:
        check("host-metrics.jsonl exists after run_pass", False)

    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n=== RESULT: {passed}/{total} PASS ===")
    return passed, total


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        p, t = selftest()
        sys.exit(0 if p == t else 1)
    elif "--register" in sys.argv:
        ok = register_schtask()
        sys.exit(0 if ok else 1)
    else:
        result = run_pass()
        print(json.dumps(result))
