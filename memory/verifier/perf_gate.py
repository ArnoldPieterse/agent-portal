#!/usr/bin/env python3
"""Goal 4: Performance Regression Gate.
Measures p50/p95 latency for read-only /api/* endpoints, stores a baseline,
and alerts when any endpoint degrades >20% vs baseline.

Usage:
  python memory/verifier/perf_gate.py --baseline   # capture/refresh baseline
  python memory/verifier/perf_gate.py              # compare vs baseline, alert on regression
Exit: 0 = clean (no regression), 1 = regression detected, 2 = portal unreachable.
"""
import json, os, sys, time, urllib.request, statistics
from datetime import datetime, timezone

BASE = "http://127.0.0.1:8099"
HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE_PATH = os.path.join(HERE, "perf-baseline.json")
REPORT_PATH = os.path.join(HERE, "perf-report.md")

# Read-only GET endpoints (mutating/POST routes intentionally excluded).
ENDPOINTS = [
    "/api/status", "/api/health/fleet", "/api/goals", "/api/agents",
    "/api/fleet", "/api/fleet/status", "/api/models", "/api/models/status",
    "/api/perf", "/api/tools", "/api/uploads", "/api/history", "/api/provenance",
    "/api/memory-health", "/api/manifest", "/api/knowledge-bases",
    "/api/run-state", "/api/activity", "/api/decisions", "/api/net/dns",
]

WARMUP = 2
SAMPLES = 10
DEGRADE_PCT = 20.0  # alert threshold


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def measure(path):
    """Return (p50_ms, p95_ms, errors) for one endpoint."""
    url = BASE + path
    samples = []
    errors = 0
    for i in range(WARMUP + SAMPLES):
        try:
            t0 = time.perf_counter()
            r = urllib.request.urlopen(url, timeout=10)
            r.read(512)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            if i >= WARMUP:
                samples.append(dt_ms)
        except Exception:
            errors += 1
    if not samples:
        return None, None, errors
    samples.sort()
    p50 = statistics.median(samples)
    p95 = samples[min(len(samples) - 1, int(round(0.95 * (len(samples) - 1))))]
    return round(p50, 2), round(p95, 2), errors


def run_all():
    results = {}
    for p in ENDPOINTS:
        p50, p95, err = measure(p)
        results[p] = {"p50_ms": p50, "p95_ms": p95, "errors": err}
    return results


def capture_baseline():
    res = run_all()
    doc = {"captured_at": now_iso(), "threshold_pct": DEGRADE_PCT, "endpoints": res}
    with open(BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
    print(f"[perf_gate] baseline captured -> {os.path.relpath(BASELINE_PATH)} ({len(res)} endpoints)")
    return doc


def compare():
    if not os.path.exists(BASELINE_PATH):
        print("[perf_gate] no baseline found; run --baseline first")
        sys.exit(2)
    with open(BASELINE_PATH, encoding="utf-8") as f:
        base = json.load(f)
    res = run_all()
    regressions = []
    rows = []
    for p in ENDPOINTS:
        b = base["endpoints"].get(p, {})
        c = res.get(p, {})
        bp50 = b.get("p50_ms")
        cp50 = c.get("p50_ms")
        if bp50 is None or cp50 is None:
            rows.append((p, bp50, cp50, "N/A", False))
            continue
        delta_pct = ((cp50 - bp50) / bp50 * 100.0) if bp50 else 0.0
        regressed = delta_pct > DEGRADE_PCT
        if regressed:
            regressions.append((p, bp50, cp50, delta_pct))
        rows.append((p, bp50, cp50, f"{delta_pct:+.1f}%", regressed))
    # report
    lines = ["# Performance Gate Report", "", f"Run: {now_iso()}", f"Baseline: {base.get('captured_at')}",
             f"Threshold: +{DEGRADE_PCT:.0f}% on p50", "",
             "| endpoint | base p50 | curr p50 | delta | regressed |", "|---|---|---|---|---|"]
    for p, b, c, d, r in rows:
        lines.append(f"| {p} | {b} | {c} | {d} | {'YES' if r else 'no'} |")
    lines += ["", f"## Regressions: {len(regressions)}", ""]
    for p, b, c, d in regressions:
        lines.append(f"- **{p}**: {b} -> {c} ms ({d:+.1f}%)")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[perf_gate] report -> {os.path.relpath(REPORT_PATH)}")
    if regressions:
        for p, b, c, d in regressions:
            print(f"  REGRESSION {p}: {b} -> {c} ms ({d:+.1f}%)")
        sys.exit(1)
    print("[perf_gate] PASS: no endpoint degraded > threshold")
    sys.exit(0)


if __name__ == "__main__":
    if "--baseline" in sys.argv:
        capture_baseline()
    else:
        compare()
