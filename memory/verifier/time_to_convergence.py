"""Time-to-Convergence (TtC) Metric.
After a perturbation event, measure wall-clock until fleet returns to steady-state.
Steady-state: no pending remediations + all agents healthy (5 consecutive probes).
Writes p50/p95/max per-event TtC to memory/ops/convergence-ttc.jsonl.
"""
import json, sys, pathlib
from datetime import datetime, timedelta

DECISION_LOG = pathlib.Path("memory/decision-log.jsonl")
PROBE_LOG = pathlib.Path("memory/fleet/probes.jsonl")
OUTPUT_FILE = pathlib.Path("memory/ops/convergence-ttc.jsonl")
TIMEOUT_MIN = 60  # If not converged by 60 min, mark TIMEOUT

# Perturbation event types to detect
PERTURBATION_TYPES = {"host_down", "model_oom", "task_spike", "agent_stall"}
# Recovery indicators: a health check showing all clear
HEALTHY_TYPE = "health_check"
CONSECUTIVE_REQUIRED = 5

def parse_log(path):
    """Parse a JSONL file into list of (timestamp, entry)."""
    if not path.exists():
        return []
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                ts = datetime.fromisoformat(e["timestamp"])
                entries.append((ts, e))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    entries.sort(key=lambda x: x[0])
    return entries

def find_perturbations(entries):
    """Find perturbation events in the log."""
    perturbations = []
    for ts, e in entries:
        etype = e.get("type", "")
        if etype in PERTURBATION_TYPES:
            perturbations.append((ts, e))
        # Also treat failed runbook executions with rolled_back=True as perturbation
        elif etype == "runbook_execution" and e.get("rolled_back") and not e.get("overall_ok"):
            perturbations.append((ts, e))
    return perturbations

def measure_ttc(pert_ts, entries):
    """Measure time-to-convergence after a perturbation.
    Looks for CONSECUTIVE_REQUIRED consecutive healthy checks after pert_ts.
    Returns (ttc_seconds or None, status)."""
    healthy_count = 0
    for ts, e in entries:
        if ts <= pert_ts:
            continue
        # Check timeout
        if (ts - pert_ts) > timedelta(minutes=TIMEOUT_MIN):
            return None, "TIMEOUT"
        
        etype = e.get("type", "")
        if etype == HEALTHY_TYPE and e.get("all_healthy", False):
            healthy_count += 1
            if healthy_count >= CONSECUTIVE_REQUIRED:
                ttc = (ts - pert_ts).total_seconds()
                return ttc, "CONVERGED"
        elif etype in PERTURBATION_TYPES:
            # New perturbation resets the counter
            healthy_count = 0
    
    # If we ran out of entries before timeout or convergence
    if entries and entries[-1][0] <= pert_ts + timedelta(minutes=TIMEOUT_MIN):
        return None, "INCOMPLETE"
    return None, "TIMEOUT"

def compute_stats(ttc_values):
    """Compute p50, p95, max from a list of TtC values (seconds)."""
    if not ttc_values:
        return {"p50": None, "p95": None, "max": None, "count": 0}
    sorted_vals = sorted(ttc_values)
    n = len(sorted_vals)
    p50_idx = min(n - 1, int(0.5 * n))
    p95_idx = min(n - 1, int(0.95 * n))
    return {
        "p50": sorted_vals[p50_idx],
        "p95": sorted_vals[p95_idx],
        "max": sorted_vals[-1],
        "count": n
    }

def run(decision_log=DECISION_LOG, probe_log=PROBE_LOG):
    """Main: find perturbations, measure TtC, write stats."""
    entries = parse_log(decision_log) + parse_log(probe_log)
    entries.sort(key=lambda x: x[0])
    
    perturbations = find_perturbations(entries)
    if not perturbations:
        print("No perturbation events found.")
        return [], 0
    
    results = []
    ttc_values = []
    for pert_ts, pert_e in perturbations:
        ttc, status = measure_ttc(pert_ts, entries)
        result = {
            "event_type": pert_e.get("type", "unknown"),
            "event_time": pert_ts.isoformat(),
            "ttc_seconds": ttc,
            "status": status
        }
        results.append(result)
        if ttc is not None:
            ttc_values.append(ttc)
    
    stats = compute_stats(ttc_values)
    
    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
        stats["recorded_at"] = datetime.now().isoformat()
        f.write(json.dumps({"_stats": True, **stats}) + "\n")
    
    # Print summary
    for r in results:
        ttc_str = f"{r['ttc_seconds']:.0f}s" if r['ttc_seconds'] else "null"
        print(f"  {r['event_type']} @ {r['event_time']}: TtC={ttc_str} ({r['status']})")
    print(f"Stats: p50={stats['p50']}, p95={stats['p95']}, max={stats['max']}, n={stats['count']}")
    
    return results, 0

def self_test():
    """Verification cases. Returns (passed, total)."""
    import tempfile, os
    passed = 0
    total = 0
    
    # Case 1: synthetic event with 4-min recovery = TtC=240s
    total += 1
    base = datetime(2026, 11, 24, 10, 0, 0)
    entries = [
        {"type": "host_down", "target": "White", "timestamp": base.isoformat()},
        # 5 consecutive healthy checks starting at +3min, every 30s (converges at 3min + 4*30s = 4min)
    ]
    for i in range(5):
        ts = base + timedelta(minutes=3, seconds=i * 30)
        entries.append({"type": "health_check", "all_healthy": True, 
                        "timestamp": ts.isoformat()})
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = pathlib.Path(f.name)
    
    try:
        all_entries = parse_log(tmp)
        perturbations = find_perturbations(all_entries)
        assert len(perturbations) == 1, f"Expected 1 perturbation, got {len(perturbations)}"
        ttc, status = measure_ttc(perturbations[0][0], all_entries)
        # 5th check at 3min + 4*30s = 300s from perturbation
        assert status == "CONVERGED", f"Expected CONVERGED, got {status}"
        assert ttc is not None and abs(ttc - 300.0) < 1.0, f"Expected ~300s, got {ttc}"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case1: {ex}")
    finally:
        os.unlink(tmp)
    
    # Case 2: never-converging event (still pending at +60min) = TIMEOUT
    total += 1
    entries = [
        {"type": "model_oom", "target": "Black", "timestamp": base.isoformat()},
        # Only 3 healthy checks before timeout window ends
    ]
    for i in range(3):
        ts = base + timedelta(minutes=5, seconds=i * 60)
        entries.append({"type": "health_check", "all_healthy": True, 
                        "timestamp": ts.isoformat()})
    # Entry well past 60 min to trigger timeout check
    entries.append({"type": "health_check", "all_healthy": False, 
                    "timestamp": (base + timedelta(minutes=61)).isoformat()})
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = pathlib.Path(f.name)
    
    try:
        all_entries = parse_log(tmp)
        perturbations = find_perturbations(all_entries)
        ttc, status = measure_ttc(perturbations[0][0], all_entries)
        assert status == "TIMEOUT", f"Expected TIMEOUT, got {status}"
        assert ttc is None, f"Expected None TtC, got {ttc}"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case2: {ex}")
    finally:
        os.unlink(tmp)
    
    # Case 3: idempotency - re-run on same log gives same values
    total += 1
    entries = [
        {"type": "host_down", "target": "White", "timestamp": base.isoformat()},
    ]
    for i in range(5):
        ts = base + timedelta(minutes=2, seconds=i * 30)
        entries.append({"type": "health_check", "all_healthy": True, 
                        "timestamp": ts.isoformat()})
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = pathlib.Path(f.name)
    
    try:
        all_entries = parse_log(tmp)
        perturbations = find_perturbations(all_entries)
        ttc1, status1 = measure_ttc(perturbations[0][0], all_entries)
        # Run again on same data
        all_entries2 = parse_log(tmp)
        perturbations2 = find_perturbations(all_entries2)
        ttc2, status2 = measure_ttc(perturbations2[0][0], all_entries2)
        assert ttc1 == ttc2, f"Idempotency failed: {ttc1} != {ttc2}"
        assert status1 == status2
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case3: {ex}")
    finally:
        os.unlink(tmp)
    
    # Case 4: multiple perturbations, stats computed correctly
    total += 1
    entries = [
        {"type": "host_down", "target": "White", "timestamp": base.isoformat()},
    ]
    # First event converges at 2min + 4*30s = 180s
    for i in range(5):
        ts = base + timedelta(minutes=2, seconds=i * 30)
        entries.append({"type": "health_check", "all_healthy": True, 
                        "timestamp": ts.isoformat()})
    # Second event at +10min, converges at +10min + 5min = 300s TtC
    base2 = base + timedelta(minutes=10)
    entries.append({"type": "model_oom", "target": "Black", "timestamp": base2.isoformat()})
    for i in range(5):
        ts = base2 + timedelta(minutes=5, seconds=i * 30)
        entries.append({"type": "health_check", "all_healthy": True, 
                        "timestamp": ts.isoformat()})
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = pathlib.Path(f.name)
    
    try:
        all_entries = parse_log(tmp)
        perturbations = find_perturbations(all_entries)
        assert len(perturbations) == 2, f"Expected 2 perturbations, got {len(perturbations)}"
        ttc_values = []
        for pts, pe in perturbations:
            ttc, status = measure_ttc(pts, all_entries)
            if ttc is not None:
                ttc_values.append(ttc)
        stats = compute_stats(ttc_values)
        assert stats["count"] == 2, f"Expected count=2, got {stats['count']}"
        assert stats["max"] >= stats["p50"], "max should be >= p50"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case4: {ex}")
    finally:
        os.unlink(tmp)
    
    # Case 5: no perturbations = clean
    total += 1
    entries = [
        {"type": "health_check", "all_healthy": True, 
         "timestamp": base.isoformat()},
        {"type": "runbook_execution", "agent": "Builder", "overall_ok": True,
         "timestamp": (base + timedelta(minutes=5)).isoformat()}
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
        tmp = pathlib.Path(f.name)
    
    try:
        all_entries = parse_log(tmp)
        perturbations = find_perturbations(all_entries)
        assert len(perturbations) == 0, f"Expected no perturbations, got {len(perturbations)}"
        passed += 1
    except AssertionError as ex:
        print(f"FAIL case5: {ex}")
    finally:
        os.unlink(tmp)
    
    print(f"\nSelf-test: {passed}/{total} passed")
    return passed, total

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        p, t = self_test()
        sys.exit(0 if p == t else 1)
    else:
        results, rc = run()
        sys.exit(rc)
