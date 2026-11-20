"""
Concurrent load test for winrm_pool.py - Mechanic Goal 1 closure step.
Runs >=5 parallel commands on WHITE (local path) to verify session pooling
handles concurrent access without corruption or deadlock.
"""
import sys, time, json, threading
sys.path.insert(0, "memory/mechanic")
from winrm_pool import WinRMPool

NUM_CONCURRENT = 8
RESULTS = []
LOCK = threading.Lock()

def worker(pool: WinRMPool, idx: int):
    t0 = time.time()
    try:
        r = pool.run_cmd("WHITE", ["cmd", "/c", f"echo worker-{idx}"])
        with LOCK:
            RESULTS.append({"idx": idx, "ok": True, "elapsed_s": round(time.time()-t0, 3),
                            "stdout": r["std_out"].strip(), "attempts": r["attempts"]})
    except Exception as e:
        with LOCK:
            RESULTS.append({"idx": idx, "ok": False, "error": str(e)})

def main():
    pool = WinRMPool()
    threads = []
    t_start = time.time()
    for i in range(NUM_CONCURRENT):
        t = threading.Thread(target=worker, args=(pool, i))
        threads.append(t)
        t.start()
    for t in threads:
        t.join(timeout=30)

    total_s = round(time.time() - t_start, 3)
    ok_count = sum(1 for r in RESULTS if r.get("ok"))
    fail_count = NUM_CONCURRENT - ok_count

    # Verify each worker got its own correct output (no cross-contamination)
    by_idx = {r["idx"]: r for r in RESULTS}
    correct_outputs = all(
        by_idx.get(i, {}).get("stdout") == f"worker-{i}" for i in range(NUM_CONCURRENT)
    )

    report = {
        "test": "concurrent_pool_load",
        "num_concurrent": NUM_CONCURRENT,
        "total_elapsed_s": total_s,
        "successes": ok_count,
        "failures": fail_count,
        "outputs_correct": correct_outputs,
        "all_passed": (ok_count == NUM_CONCURRENT and correct_outputs),
        "details": sorted(RESULTS, key=lambda x: x["idx"]),
    }

    out_path = "memory/mechanic/goal1-concurrent-test-2026-11-20.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps({k: v for k, v in report.items() if k != "details"}, indent=2))
    print(f"\nFull report: {out_path}")
    return 0 if report["all_passed"] else 1

if __name__ == "__main__":
    sys.exit(main())
