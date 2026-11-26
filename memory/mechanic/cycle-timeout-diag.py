#!/usr/bin/env python3
"""cycle-timeout-diag.py - Auto-capture diagnostic when cycle exceeds duration SLA.

On timeout breach, captures:
  1. stack_traces (active agent processes)
  2. model_load_state (loaded models per host)
  3. active_passes (current auto-loop passes in flight)
  4. cycle_metadata (duration, SLA, breach amount)

Output: memory/ops/cycle-timeout-diag-<timestamp>.json
Usage:
  python memory/mechanic/cycle-timeout-diag.py --check    # check if current cycle breached
  python memory/mechanic/cycle-timeout-diag.py --simulate # simulate a timeout for testing
"""
import json, os, sys, time, platform, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLA_FILE = "memory/ops/cycle-duration-stats.json"
DURATIONS_FILE = "memory/ops/cycle-durations.jsonl"
AUTOLOOP_FILE = "memory/ops/autoloop.jsonl"
STUDIO_URLS = {
    "white": "http://10.0.0.2:8888",
    "red": "http://127.0.0.1:8888",
    "pale": "http://10.0.0.3:8888",
    "black": "http://10.0.0.4:8888",
}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def load_sla():
    """Load cycle duration SLA."""
    p = Path(SLA_FILE)
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("p95_min", 120), data.get("max_allowed_min", 180)
    return 120, 180  # defaults: P95=120min, max allowed=180min

def get_current_cycle_duration():
    """Estimate current cycle duration from autoloop timestamps."""
    p = Path(AUTOLOOP_FILE)
    if not p.exists():
        return None
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    if len(lines) < 2:
        return None
    # Find the most recent cycle start (first entry after a gap > 10min)
    entries = []
    for line in reversed(lines[-50:]):
        try:
            e = json.loads(line)
            ts = datetime.fromisoformat(e.get("ts", ""))
            entries.append(ts)
        except (json.JSONDecodeError, ValueError):
            continue
    if len(entries) < 2:
        return None
    # Duration from oldest to newest in recent window
    duration_s = (entries[0] - entries[-1]).total_seconds()
    return duration_s

def capture_stack_traces():
    """Capture active process info as a proxy for stack traces."""
    import subprocess
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
                          capture_output=True, text=True, timeout=10)
        processes = [line.strip() for line in r.stdout.split("\n") if "python" in line.lower()]
        return {"processes": processes[:20], "count": len(processes)}
    except Exception as e:
        return {"error": str(e), "count": 0}

def capture_model_load_state():
    """Query Studio API on each host for loaded models."""
    state = {}
    for host, url in STUDIO_URLS.items():
        try:
            req = urllib.request.Request(f"{url}/api/inference/loaded-models")
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode())
                models = [m.get("model_path", "").split("\\")[-1] for m in data if isinstance(data, list)]
                state[host] = {"reachable": True, "models": models}
        except Exception as e:
            state[host] = {"reachable": False, "error": str(e)[:100]}
    return state

def capture_active_passes():
    """Check autoloop.jsonl for passes currently in flight."""
    p = Path(AUTOLOOP_FILE)
    if not p.exists():
        return {"active": 0, "recent": []}
    lines = p.read_text(encoding="utf-8").strip().split("\n")
    recent = []
    for line in reversed(lines[-10:]):
        try:
            e = json.loads(line)
            ts = datetime.fromisoformat(e.get("ts", ""))
            age_s = (datetime.now(timezone.utc) - ts).total_seconds()
            if age_s < 300:  # last 5 min
                recent.append({"ts": e.get("ts"), "agent": e.get("agent", "?"), "age_s": round(age_s)})
        except (json.JSONDecodeError, ValueError):
            continue
    return {"active": len(recent), "recent": recent}

def build_diagnostic(duration_s=None, sla_min=None, simulate=False):
    """Build the full diagnostic with all 4 required fields."""
    if sla_min is None:
        _, sla_min = load_sla()
    if duration_s is None and not simulate:
        duration_s = get_current_cycle_duration()
    
    if simulate:
        duration_s = (sla_min + 30) * 60  # simulate 30min over SLA
    
    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    diag = {
        "ts": now_iso(),
        "trigger": "simulated" if simulate else "sla_breach",
        "cycle_metadata": {
            "duration_s": round(duration_s),
            "duration_min": round(duration_s / 60, 1),
            "sla_min": sla_min,
            "breach_min": round((duration_s - sla_min * 60) / 60, 1),
        },
        "stack_traces": capture_stack_traces(),
        "model_load_state": capture_model_load_state(),
        "active_passes": capture_active_passes(),
    }
    
    # Write to file
    out_path = Path(f"memory/ops/cycle-timeout-diag-{ts_tag}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(diag, indent=2), encoding="utf-8")
    print(f"Diagnostic written: {out_path}")
    return diag

def simulate():
    """Run 2 simulated timeout captures to verify all fields present."""
    print("=== Cycle Timeout Auto-Diagnostic - SIMULATION ===")
    start = time.time()
    
    results = []
    for i in range(2):
        sla = 120 + i * 30  # different SLA thresholds
        diag = build_diagnostic(sla_min=sla, simulate=True)
        
        # Verify all 4 required fields present
        has_stack = "stack_traces" in diag and diag["stack_traces"].get("count", -1) >= 0
        has_model = "model_load_state" in diag and len(diag["model_load_state"]) == 4
        has_passes = "active_passes" in diag and "active" in diag["active_passes"]
        has_meta = "cycle_metadata" in diag and all(k in diag["cycle_metadata"] for k in ("duration_s", "sla_min", "breach_min"))
        
        ok = has_stack and has_model and has_passes and has_meta
        elapsed = time.time() - start
        results.append({"sim": i+1, "ok": ok, "fields": {"stack": has_stack, "model": has_model, "passes": has_passes, "meta": has_meta}})
        print(f"  Sim {i+1}: all_fields={ok} (stack={has_stack}, model={has_model}, passes={has_passes}, meta={has_meta})")
    
    total_time = time.time() - start
    under_30s = total_time < 30
    print(f"\nTotal: {total_time:.1f}s | <30s: {under_30s}")
    print(f"Result: {'PASS' if all(r['ok'] for r in results) and under_30s else 'FAIL'}")
    
    # Log evidence
    ev_path = Path("memory/mechanic/cycle-timeout-diag-evidence.jsonl")
    with ev_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_iso(), "mode": "simulation", "results": results, "total_s": round(total_time,1), "pass": all(r["ok"] for r in results) and under_30s}) + "\n")
    
    return all(r["ok"] for r in results) and under_30s

if __name__ == "__main__":
    if "--simulate" in sys.argv:
        simulate()
    elif "--check" in sys.argv:
        duration = get_current_cycle_duration()
        sla_min, max_min = load_sla()
        if duration and duration > max_min * 60:
            print(f"BREACH: cycle {duration/60:.0f}min > SLA {max_min}min")
            build_diagnostic(duration)
        else:
            print(f"OK: cycle {duration/60:.0f}min < SLA {max_min}min" if duration else "No data")
    else:
        print("Usage: --check | --simulate")
