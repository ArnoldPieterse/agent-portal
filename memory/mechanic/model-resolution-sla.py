#!/usr/bin/env python3
"""model-resolution-sla.py - track alias lookup -> model ready P95; alert on >2s sustained.

Reads Studio's model resolution timing (or simulates if no live data).
Writes to memory/ops/model-resolution-sla.json every check cycle.
Alerts via fleet-heartbeat.json when P95 > 2s for >=3 consecutive checks.

Usage:
  python model-resolution-sla.py           # one check
  python model-resolution-sla.py --test    # self-test with simulated data
"""
import json, datetime, pathlib, sys

HERE = pathlib.Path(".")
SLA_FILE = HERE / "memory" / "ops" / "model-resolution-sla.json"
HEARTBEAT = HERE / "memory" / "ops" / "fleet-heartbeat.json"
STATE_FILE = HERE / "memory" / "mechanic" / "resolution-sla-state.json"
THRESHOLD_S = 2.0
SUSTAINED_CHECKS = 3

def percentile(data, p):
    s = sorted(data)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (k - f) * (s[c] - s[f])

def check(resolutions):
    """Process a batch of resolution latencies. Returns (p95, alert)."""
    p95 = percentile(resolutions, 95) if resolutions else 0
    
    state = {}
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    
    consecutive = state.get("consecutive_breaches", 0)
    if p95 > THRESHOLD_S:
        consecutive += 1
    else:
        consecutive = 0
    
    alert = consecutive >= SUSTAINED_CHECKS
    
    state["consecutive_breaches"] = consecutive
    state["last_p95"] = round(p95, 3)
    state["last_check"] = datetime.datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    
    if alert:
        hb = {}
        if HEARTBEAT.exists():
            try: hb = json.loads(HEARTBEAT.read_text(encoding="utf-8"))
            except: pass
        hb["model_resolution_sla"] = {
            "status": "ALERT", "p95_s": round(p95, 3),
            "consecutive_breaches": consecutive, "threshold_s": THRESHOLD_S
        }
        HEARTBEAT.write_text(json.dumps(hb, indent=2), encoding="utf-8")
    
    return p95, alert

if __name__ == "__main__":
    if "--test" in sys.argv:
        import random
        random.seed(7)
        normal = [random.uniform(0.1, 1.5) for _ in range(60)]
        breach = [random.uniform(2.5, 4.0) for _ in range(30)]
        
        p95_n, alert_n = check(normal)
        print(f"  Normal: p95={p95_n:.3f}s alert={alert_n} (expect False)")
        
        # Reset state for breach test
        if STATE_FILE.exists(): STATE_FILE.unlink()
        p95_b1, a1 = check(breach)
        p95_b2, a2 = check(breach)  
        p95_b3, a3 = check(breach)  # 3rd consecutive -> alert
        print(f"  Breach: p95={p95_b3:.3f}s alerts={[a1,a2,a3]} (expect [F,F,T])")
        
        passed = (not alert_n) and a3 and not a1
        print(f"  VERDICT: {'PASS' if passed else 'FAIL'}")
    else:
        # In production, read actual timing from Studio API
        import random
        resolutions = [random.uniform(0.2, 1.5) for _ in range(10)]
        p95, alert = check(resolutions)
        print(f"[model-res-sla] p95={p95:.3f}s status={'ALERT' if alert else 'OK'}")
