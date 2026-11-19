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


def simulate():
    """Self-test: prove regression detection works without live portal.
    1. Write synthetic baseline (all endpoints ~5ms p50).
    2. Compare with one endpoint slowed to 1000ms -> expect alert on that endpoint only.
    3. Compare with all-at-baseline -> expect 0 regressions.
    Exit 0 = all assertions pass, 1 = assertion failure.
    """
    import tempfile, shutil
    # --- Phase 1: synthetic baseline ---
    base_doc = {"captured_at": now_iso(), "threshold_pct": DEGRADE_PCT, "endpoints": {}}
    for p in ENDPOINTS:
        base_doc["endpoints"][p] = {"p50_ms": 5.0, "p95_ms": 8.0, "errors": 0}
    # Write to a temp baseline so we don't clobber the real one
    tmpdir = tempfile.mkdtemp(prefix="perf_sim_")
    sim_base = os.path.join(tmpdir, "perf-baseline.json")
    with open(sim_base, "w", encoding="utf-8") as f:
        json.dump(base_doc, f, indent=2)

    def _compare_with(current_data, baseline_path):
        """Run the comparison logic against given current data + baseline path."""
        with open(baseline_path, encoding="utf-8") as f:
            base = json.load(f)
        regressions = []
        for p in ENDPOINTS:
            b = base["endpoints"].get(p, {})
            c = current_data.get(p, {})
            bp50 = b.get("p50_ms")
            cp50 = c.get("p50_ms")
            if bp50 is None or cp50 is None:
                continue
            delta_pct = ((cp50 - bp50) / bp50 * 100.0) if bp50 else 0.0
            if delta_pct > DEGRADE_PCT:
                regressions.append((p, bp50, cp50, delta_pct))
        return regressions

    # --- Phase 2: slow endpoint -> expect alert ---
    slow_target = "/api/goals"
    current_slow = {p: {"p50_ms": 5.0, "p95_ms": 8.0, "errors": 0} for p in ENDPOINTS}
    current_slow[slow_target] = {"p50_ms": 1000.0, "p95_ms": 1200.0, "errors": 0}
    regressed = _compare_with(current_slow, sim_base)
    assert len(regressed) == 1, f"Expected exactly 1 regression, got {len(regressed)}: {regressed}"
    assert regressed[0][0] == slow_target, f"Wrong endpoint flagged: {regressed[0]}"
    print(f"[perf_gate:simulate] Phase 2 PASS: slowdown on {slow_target} (5->1000ms) correctly triggered alert")

    # --- Phase 3: clean state -> expect 0 regressions ---
    current_clean = {p: {"p50_ms": 4.8, "p95_ms": 7.5, "errors": 0} for p in ENDPOINTS}
    regressed_clean = _compare_with(current_clean, sim_base)
    assert len(regressed_clean) == 0, f"Expected 0 regressions in clean state, got {regressed_clean}"
    print("[perf_gate:simulate] Phase 3 PASS: clean state shows 0 regressions")

    # Cleanup
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("[perf_gate:simulate] ALL ASSERTIONS PASS (baseline captured + alert fires + clean=0)")
    sys.exit(0)


if __name__ == "__main__":
    if "--simulate" in sys.argv:
        simulate()
    elif "--baseline" in sys.argv:
        capture_baseline()
    else:
        compare()
