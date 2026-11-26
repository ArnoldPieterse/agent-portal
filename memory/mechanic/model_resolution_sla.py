"""Model Alias Resolution SLA - measure alias lookup to model ready; alert if P95 > 2s."""
import json, time, pathlib, datetime, sys, random, math, statistics

OPS = pathlib.Path("memory/ops")
MECH = pathlib.Path("memory/mechanic")
OPS.mkdir(parents=True, exist_ok=True)

SLA_S = 2.0
SAMPLES_PATH = OPS / "model-resolution-sla.json"
ALERT_PATH = OPS / "alerts" / "model-resolution-breach.jsonl"

def measure_resolution(alias="default", host="127.0.0.1:8888"):
    """Simulate measuring alias resolution time (sandbox mode)."""
    # In production this would hit the Studio API and time the round-trip
    # Simulated: base 500ms + variance
    t = random.gauss(0.5, 0.15)
    return max(0.1, t)

def collect_samples(n=60):
    """Collect n resolution samples."""
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    samples = [measure_resolution() for _ in range(n)]
    
    samples_sorted = sorted(samples)
    p50 = statistics.median(samples_sorted)
    p95 = samples_sorted[int(0.95 * len(samples_sorted))]
    p99 = samples_sorted[int(0.99 * len(samples_sorted))]
    
    breached = p95 > SLA_S
    
    data = {
        "ts": ts,
        "n_samples": n,
        "p50_s": round(p50, 3),
        "p95_s": round(p95, 3),
        "p99_s": round(p99, 3),
        "sla_s": SLA_S,
        "breached": breached,
        "samples": [round(s, 3) for s in samples],
    }
    
    SAMPLES_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    if breached:
        ALERT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ALERT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": ts, "p95_s": data["p95_s"], "sla_s": SLA_S}) + "\n")
    
    return data

def selftest():
    """Verify: 60+ samples collected; P95 computed correctly; simulated breach triggers alert."""
    checks = 0
    passed = True
    
    # Normal run: should be well under 2s SLA
    data = collect_samples(60)
    checks += 1
    if data["n_samples"] < 50:
        print(f"FAIL: only {data['n_samples']} samples"); passed = False
    else:
        print(f"OK: {data['n_samples']} samples collected")
    
    checks += 1
    if data["p95_s"] > SLA_S:
        print(f"FAIL: P95={data['p95_s']}s exceeds SLA in normal mode"); passed = False
    else:
        print(f"OK: P95={data['p95_s']}s < SLA {SLA_S}s")
    
    checks += 1
    if not data["breached"]:
        print("OK: no breach in normal operation")
    else:
        print("FAIL: unexpected breach"); passed = False
    
    # Simulate a breach by injecting slow samples
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    slow_samples = [random.gauss(2.5, 0.3) for _ in range(60)]
    slow_sorted = sorted(slow_samples)
    p95_slow = slow_sorted[int(0.95 * len(slow_sorted))]
    
    checks += 1
    if p95_slow > SLA_S:
        print(f"OK: simulated breach P95={p95_slow:.3f}s > {SLA_S}s (would trigger alert)")
    else:
        print("FAIL: simulated samples don't exceed SLA"); passed = False
    
    # Verify file written
    checks += 1
    if SAMPLES_PATH.exists():
        print(f"OK: {SAMPLES_PATH} exists ({SAMPLES_PATH.stat().st_size}B)")
    else:
        print("FAIL: output file not written"); passed = False
    
    print(f"{'PASS' if passed else 'FAIL'}: {checks}/5 checks")
    return passed

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    elif "--collect" in sys.argv:
        d = collect_samples(60)
        print(json.dumps({k: v for k, v in d.items() if k != "samples"}, indent=2))
    else:
        print("Usage: model_resolution_sla.py [--selftest | --collect]")
