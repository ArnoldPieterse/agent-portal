"""Network Connectivity Probe - tests TCP to all 4 fleet hosts.
Usage: python memory/mechanic/net_probe.py [--once | --schedule]"""
import socket, time, json, os, sys
from datetime import datetime, timezone

HOSTS = {
    "white": ("127.0.0.1", 8099),
    "black": ("127.0.0.1", 8099),  # same portal in sandbox; real host would differ
    "red":   ("127.0.0.1", 8099),
    "blue":  ("127.0.0.1", 8099),
}
LOG = os.path.join(os.path.dirname(__file__), "net_probe_log.jsonl")
FAIL_THRESHOLD = 3
LATENCY_P95_ALERT_MS = 200
INTERVAL_S = 600  # 10 min

fail_counts = {h: 0 for h in HOSTS}
latencies = {h: [] for h in HOSTS}

def probe_host(name, addr, port):
    start = time.perf_counter()
    try:
        s = socket.create_connection((addr, port), timeout=5)
        ms = (time.perf_counter() - start) * 1000
        s.close()
        return True, ms, None
    except Exception as e:
        ms = (time.perf_counter() - start) * 1000
        return False, ms, str(e)

def run_check():
    ts = datetime.now(timezone.utc).isoformat()
    results = {}
    alerts = []
    for name, (addr, port) in HOSTS.items():
        ok, ms, err = probe_host(name, addr, port)
        if ok:
            fail_counts[name] = 0
            latencies[name].append(ms)
        else:
            fail_counts[name] += 1
            if fail_counts[name] > FAIL_THRESHOLD:
                alerts.append(f"{name}: {fail_counts[name]} consecutive failures")
        results[name] = {"reachable": ok, "latency_ms": round(ms, 2), "error": err}
    # p95 check
    for name in HOSTS:
        if len(latencies[name]) >= 10:
            sorted_l = sorted(latencies[name][-100:])
            p95 = sorted_l[int(len(sorted_l) * 0.95)]
            results[name]["p95_ms"] = round(p95, 2)
            if p95 > LATENCY_P95_ALERT_MS:
                alerts.append(f"{name}: p95={p95:.1f}ms > {LATENCY_P95_ALERT_MS}ms")
    entry = {"ts": ts, "results": results, "alerts": alerts}
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    status = "DEGRADED" if alerts else "HEALTHY"
    for name, r in results.items():
        mark = "PASS" if r["reachable"] else "FAIL"
        print(f"  [{mark}] {name}: {r['latency_ms']}ms {'(' + r['error'] + ')' if r['error'] else ''}")
    for a in alerts:
        print(f"  [ALERT] {a}")
    print(f"Overall: {status}")
    return status

def main():
    mode = "--once" if "--once" in sys.argv else ("--schedule" if "--schedule" in sys.argv else "--once")
    if mode == "--schedule":
        print(f"Scheduling net_probe every {INTERVAL_S}s...")
        while True:
            run_check()
            time.sleep(INTERVAL_S)
    else:
        run_check()

if __name__ == "__main__":
    main()