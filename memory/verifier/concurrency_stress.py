"""Concurrency Stress Test - Goal #6
Fires 50 parallel requests at /api/goals + /api/fleet/overview simultaneously.
Measures p95 latency, error rate, and memory usage.
Target: p95 <500ms, 0 errors.

Usage: python memory/verifier/concurrency_stress.py [--url http://localhost:8099]
"""
import argparse
import concurrent.futures
import json
import os
import statistics
import sys
import time
import urllib.request
import urllib.error


def make_request(url: str) -> dict:
    """Single request: returns {status, latency_ms, error}"""
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "stress-test/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read()
            latency = (time.perf_counter() - t0) * 1000
            return {"status": resp.status, "latency_ms": latency, "error": None, "bytes": len(body)}
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        return {"status": 0, "latency_ms": latency, "error": str(e), "bytes": 0}


def get_memory_mb() -> float:
    """Get current process memory in MB (best-effort cross-platform)."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Linux: KB->MB
    except ImportError:
        pass
    try:
        import ctypes
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return (stat.ullTotalPhys - stat.ullAvailPhys) / (1024 * 1024)
    except Exception:
        return -1.0


def percentile(data, pct):
    """Calculate percentile without numpy."""
    if not data:
        return 0
    s = sorted(data)
    k = (len(s) - 1) * pct / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] * (c - k) + s[c] * (k - f)


def main():
    parser = argparse.ArgumentParser(description="Concurrency stress test for portal API")
    parser.add_argument("--url", default="http://localhost:8099", help="Base URL")
    parser.add_argument("--concurrency", type=int, default=50, help="Parallel requests per endpoint")
    parser.add_argument("--report", default=None, help="Output report path (default: auto)")
    args = parser.parse_args()

    endpoints = [
        f"{args.url}/api/goals",
        f"{args.url}/api/fleet/overview",
    ]

    total_requests = len(endpoints) * args.concurrency
    mem_before = get_memory_mb()
    t_start = time.perf_counter()

    results = {ep: [] for ep in endpoints}

    # Fire all requests concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=total_requests) as pool:
        futures = {}
        for ep in endpoints:
            for _ in range(args.concurrency):
                f = pool.submit(make_request, ep)
                futures[f] = ep
        for f in concurrent.futures.as_completed(futures):
            ep = futures[f]
            results[ep].append(f.result())

    total_time = time.perf_counter() - t_start
    mem_after = get_memory_mb()

    # Aggregate metrics
    report_lines = [
        "# Concurrency Stress Test Report",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Target: p95 < 500ms, 0 errors",
        f"Total requests: {total_requests} ({args.concurrency} per endpoint)",
        f"Wall time: {total_time:.3f}s",
        f"Memory (process): {mem_before:.1f} MB -> {mem_after:.1f} MB (delta: {mem_after - mem_before:+.1f} MB)",
        "",
    ]

    all_pass = True
    for ep in endpoints:
        r = results[ep]
        latencies = [x["latency_ms"] for x in r if x["error"] is None]
        errors = [x for x in r if x["error"] is not None or x["status"] != 200]
        p95 = percentile(latencies, 95) if latencies else -1
        p50 = percentile(latencies, 50) if latencies else -1
        avg = statistics.mean(latencies) if latencies else -1
        max_lat = max(latencies) if latencies else -1

        report_lines.append(f"## {ep}")
        report_lines.append(f"- Requests: {len(r)}")
        report_lines.append(f"- Errors: {len(errors)} ({len(errors)/len(r)*100:.1f}%)")
        report_lines.append(f"- Latency ms: avg={avg:.1f}, p50={p50:.1f}, p95={p95:.1f}, max={max_lat:.1f}")
        if errors:
            sample = errors[0]
            report_lines.append(f"- Sample error: {sample.get('error') or f'status={sample[chr(34)+chr(34)]}'}")

        passed = p95 < 500 and len(errors) == 0
        report_lines.append(f"- **PASS**" if passed else f"- **FAIL** (p95={'<500' if p95<500 else '>500'}ms, errors={len(errors)})")
        report_lines.append("")
        if not passed:
            all_pass = False

    report_lines.append(f"## Overall: {'PASS' if all_pass else 'FAIL'}")
    report = "\n".join(report_lines)

    # Write report
    out = args.report or "memory/verifier/concurrency-stress-report.md"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write(report + "\n")

    print(report)
    print(f"\nReport written to: {out}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
