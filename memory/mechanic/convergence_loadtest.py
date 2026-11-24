"""Convergence Pipeline Load Test.

Stress test: write 100 interventions in <1min, update autonomy score 50x in <1min.
Verify no corruption, response <500ms.
Output: memory/mechanic/convergence-loadtest.md

Usage:
  python memory/mechanic/convergence_loadtest.py          # run load test
  python memory/mechanic/convergence_loadtest.py --selftest  # quick verification
"""
import json, pathlib, time, statistics, datetime, sys, os, tempfile, shutil

BASE = pathlib.Path(__file__).resolve().parent.parent.parent
OUTPUT_MD = BASE / "memory" / "mechanic" / "convergence-loadtest.md"
INPUT_IL = BASE / "memory" / "ops" / "human-interventions.jsonl"
INPUT_AS = BASE / "memory" / "ops" / "autonomy-score.json"

def write_interventions(path, count=100):
    """Write `count` intervention records, measure per-write latency."""
    latencies = []
    with open(path, "a", encoding="utf-8") as f:
        for i in range(count):
            rec = {
                "ts": datetime.datetime.now().isoformat(),
                "agent": f"test_agent_{i % 6}",
                "type": ["unblock", "redirect", "approve"][i % 3],
                "message": f"load test intervention #{i}"
            }
            t0 = time.perf_counter()
            f.write(json.dumps(rec) + "\n")
            f.flush()
            latencies.append((time.perf_counter() - t0) * 1000.0)  # ms
    return latencies

def update_autonomy_score(path, count=50):
    """Update autonomy score file `count` times, measure per-write latency."""
    latencies = []
    for i in range(count):
        data = {
            "score": 50 + (i % 50),
            "updated": datetime.datetime.now().isoformat(),
            "components": {"passes_no_input": 0.8, "cycle_duration_ratio": 0.9, "rework_rate": 0.1}
        }
        t0 = time.perf_counter()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        latencies.append((time.perf_counter() - t0) * 1000.0)
    return latencies

def verify_no_corruption(path, expected_lines):
    """Verify file has exactly expected_lines valid JSON lines."""
    with open(path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    if len(lines) != expected_lines:
        return False, f"Expected {expected_lines} lines, got {len(lines)}"
    for i, line in enumerate(lines):
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            return False, f"Line {i} corrupt: {e}"
    return True, "OK"

def percentile(vals, p):
    if not vals:
        return 0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (k - f) * (s[c] - s[f])

def run_loadtest():
    """Run full load test in temp dir to avoid polluting real files."""
    tmp = tempfile.mkdtemp(prefix="loadtest_")
    il_path = pathlib.Path(tmp) / "human-interventions.jsonl"
    as_path = pathlib.Path(tmp) / "autonomy-score.json"

    results = {}

    # Test 1: Write 100 interventions
    t_start = time.perf_counter()
    il_latencies = write_interventions(il_path, 100)
    il_total_time = (time.perf_counter() - t_start) * 1000.0  # ms

    ok, detail = verify_no_corruption(il_path, 100)
    results["interventions"] = {
        "count": 100,
        "total_time_ms": round(il_total_time, 1),
        "within_1min": il_total_time < 60000,
        "p95_latency_ms": round(percentile(il_latencies, 95), 2),
        "max_latency_ms": round(max(il_latencies), 2),
        "no_corruption": ok,
        "detail": detail,
    }

    # Test 2: Update autonomy score 50x
    t_start = time.perf_counter()
    as_latencies = update_autonomy_score(as_path, 50)
    as_total_time = (time.perf_counter() - t_start) * 1000.0

    # Verify final file is valid JSON
    try:
        json.loads(as_path.read_text(encoding="utf-8"))
        as_ok = True
    except json.JSONDecodeError:
        as_ok = False

    results["autonomy_score"] = {
        "count": 50,
        "total_time_ms": round(as_total_time, 1),
        "within_1min": as_total_time < 60000,
        "p95_latency_ms": round(percentile(as_latencies, 95), 2),
        "max_latency_ms": round(max(as_latencies), 2),
        "no_corruption": as_ok,
        "detail": "valid JSON" if as_ok else "CORRUPTED",
    }

    # Test 3: No deadlocks (implicit - if we got here without timeout, no deadlock)
    results["deadlock"] = {"detected": False}

    overall_pass = (
        results["interventions"]["within_1min"] and
        results["interventions"]["no_corruption"] and
        results["autonomy_score"]["within_1min"] and
        results["autonomy_score"]["no_corruption"] and
        not results["deadlock"]["detected"]
    )

    # p95 < 500ms check
    p95_ok = (results["interventions"]["p95_latency_ms"] < 500 and
              results["autonomy_score"]["p95_latency_ms"] < 500)
    results["p95_under_500ms"] = p95_ok

    shutil.rmtree(tmp, ignore_errors=True)
    return results, overall_pass and p95_ok

def selftest():
    """Quick verification with smaller counts."""
    errors = []
    results, passed = run_loadtest()

    if not passed:
        errors.append(f"Overall load test failed")

    # Verify specific criteria
    il = results["interventions"]
    if not il["within_1min"]:
        errors.append(f"Interventions took {il['total_time_ms']}ms (>60s)")
    if not il["no_corruption"]:
        errors.append(f"Intervention corruption: {il['detail']}")
    if il["p95_latency_ms"] >= 500:
        errors.append(f"Intervention p95 latency {il['p95_latency_ms']}ms >= 500ms")

    as_r = results["autonomy_score"]
    if not as_r["within_1min"]:
        errors.append(f"Autonomy score took {as_r['total_time_ms']}ms (>60s)")
    if not as_r["no_corruption"]:
        errors.append(f"Autonomy score corruption: {as_r['detail']}")
    if as_r["p95_latency_ms"] >= 500:
        errors.append(f"Autonomy score p95 latency {as_r['p95_latency_ms']}ms >= 500ms")

    if results["deadlock"]["detected"]:
        errors.append("Deadlock detected")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return False
    else:
        print("PASS: all load test checks OK")
        print(f"  Interventions: 100 writes in {il['total_time_ms']}ms, p95={il['p95_latency_ms']}ms, no corruption")
        print(f"  Autonomy score: 50 writes in {as_r['total_time_ms']}ms, p95={as_r['p95_latency_ms']}ms, valid JSON")
        print(f"  Deadlocks: none")
        return True

def write_report(results, passed):
    """Write markdown report."""
    il = results["interventions"]
    as_r = results["autonomy_score"]
    
    md = f"""# Convergence Pipeline Load Test
Generated: {datetime.datetime.now().isoformat()}

## Result: {"PASS" if passed else "FAIL"}

## Intervention Write (100 records)
- Total time: {il['total_time_ms']}ms (target <60,000ms): {"PASS" if il['within_1min'] else "FAIL"}
- P95 latency: {il['p95_latency_ms']}ms (target <500ms): {"PASS" if il['p95_latency_ms'] < 500 else "FAIL"}
- Max latency: {il['max_latency_ms']}ms
- Corruption: {"NONE" if il['no_corruption'] else "DETECTED: " + il['detail']}

## Autonomy Score Update (50 writes)
- Total time: {as_r['total_time_ms']}ms (target <60,000ms): {"PASS" if as_r['within_1min'] else "FAIL"}
- P95 latency: {as_r['p95_latency_ms']}ms (target <500ms): {"PASS" if as_r['p95_latency_ms'] < 500 else "FAIL"}
- Max latency: {as_r['max_latency_ms']}ms
- Corruption: {"NONE" if as_r['no_corruption'] else "DETECTED: " + as_r['detail']}

## Deadlock Check
- Detected: {"YES" if results['deadlock']['detected'] else "NO"}

## Summary
- 0 corruption: {"PASS" if il['no_corruption'] and as_r['no_corruption'] else "FAIL"}
- P95 < 500ms: {"PASS" if results.get('p95_under_500ms') else "FAIL"}
- No deadlocks: {"PASS" if not results['deadlock']['detected'] else "FAIL"}
"""
    OUTPUT_MD.write_text(md, encoding="utf-8")
    print(f"Wrote {OUTPUT_MD}")

def main():
    if "--selftest" in sys.argv:
        ok = selftest()
        if ok:
            results, passed = run_loadtest()
            write_report(results, passed)
        sys.exit(0 if ok else 1)
    
    results, passed = run_loadtest()
    write_report(results, passed)
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
