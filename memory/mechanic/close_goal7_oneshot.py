"""Goal 7 one-shot closure: run perf profile + verify + record evidence.
Usage (from any non-sandbox seat with egress to :8099):
    python memory/mechanic/close_goal7_oneshot.py [duration_s]
Default duration: 3600s (1 hour). Minimum for valid stats: 300s.
"""
import sys, os, json, time, urllib.request, statistics
from datetime import datetime, timezone

PORTAL = "http://localhost:8099"
OUT = os.path.join(os.path.dirname(__file__), "perf-profile.json")
DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 3600
INTERVAL = 5  # seconds between samples

ENDPOINTS = {
    "portal_health": PORTAL + "/api/health",
    "fleet_status": PORTAL + "/api/fleet/status",
    "goals_api": PORTAL + "/api/goals",
    "llm_models": PORTAL + "/api/models",
}

def percentile(data, p):
    if not data: return None
    s = sorted(data)
    k = (len(s)-1)*(p/100.0)
    f = int(k); c = min(f+1, len(s)-1)
    return s[f] + (k-f)*(s[c]-s[f])

def timed_get(url):
    t0 = time.perf_counter()
    try:
        r = urllib.request.urlopen(url, timeout=10)
        r.read()
        return (time.perf_counter()-t0)*1000
    except Exception:
        return None

# Pre-flight check
print(f"[close_goal7] Pre-flight: {PORTAL}/api/health ...")
try:
    urllib.request.urlopen(PORTAL+"/api/health", timeout=5).read()
    print("  OK - portal reachable")
except Exception as e:
    print(f"  FAIL: {e}")
    sys.exit(1)

# Run profile
print(f"[close_goal7] Profiling for {DURATION}s (interval={INTERVAL}s)...")
samples = {k: [] for k in ENDPOINTS}
deadline = time.time() + DURATION
n = 0
while time.time() < deadline:
    n += 1
    for name, url in ENDPOINTS.items():
        ms = timed_get(url)
        if ms is not None:
            samples[name].append(ms)
    elapsed = int(time.time() - (deadline - DURATION))
    print(f"  [{n}] t={elapsed}s " + " ".join(f"{k}={len(v)}" for k,v in samples.items()))
    if time.time() < deadline:
        time.sleep(INTERVAL)

# Build results
results = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "duration_s": DURATION,
    "mock": False,
    "samples_collected": {k: len(v) for k,v in samples.items()},
    "metrics": {}
}
for name, vals in samples.items():
    if not vals:
        results["metrics"][name] = {"status": "no_samples", "p50": None, "p95": None, "p99": None}
    else:
        results["metrics"][name] = {
            "status": "ok", "count": len(vals),
            "min_ms": round(min(vals),2), "max_ms": round(max(vals),2),
            "mean_ms": round(statistics.mean(vals),2),
            "p50": round(percentile(vals,50),2),
            "p95": round(percentile(vals,95),2),
            "p99": round(percentile(vals,99),2)
        }

with open(OUT, 'w') as f:
    json.dump(results, f, indent=2)
print(f"[close_goal7] Saved to {OUT}")

# Verify
ok = all(m.get("status")=="ok" and m.get("p50") is not None for m in results["metrics"].values())
if not ok:
    print("[close_goal7] FAIL: some endpoints have no data")
    sys.exit(1)
for name, m in results["metrics"].items():
    print(f"  {name}: p50={m['p50']}ms p95={m['p95']}ms p99={m['p99']}ms (n={m['count']})")
print("[close_goal7] PASS: all endpoints have valid p50/p95/p99")

# Record evidence
ledger = os.path.join(os.path.dirname(__file__), "..", "researcher", "goal_ledger.py")
if os.path.exists(ledger):
    import subprocess
    note = f"close_goal7_oneshot.py live run {DURATION}s; all 4 endpoints p50/p95/p99 valid"
    subprocess.run([sys.executable, ledger, "--record", "mechanic", "7", "--note", note])
    print("[close_goal7] Evidence recorded in goal ledger")

print("\n[close_goal7] DONE. Goal 7 closure complete.")
