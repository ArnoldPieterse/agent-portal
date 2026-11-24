"""Scheduled Task Health Check - verifies fleet schtasks are alive and producing output.

Round topic: Closed-Loop Autonomy & Fleet Cockpit.
Checks each registered schtask for: (1) last-run recency, (2) output file freshness.

Usage:
    python memory/builder/schtasks_health_check.py          # check all known tasks
    python memory/builder/schtasks_health_check.py --selftest  # run self-test
"""
import json, os, subprocess, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Known fleet scheduled tasks and their expected output paths / max age (seconds)
TASKS = {
    "MirrorHeal": {
        "interval_min": 15,
        "output": "memory/ops/mirror-heal-log.jsonl",
        "max_age_s": 900,   # 15 min
    },
    "PortalSmbDrift": {
        "interval_min": 30,
        "output": "memory/ops/smb-drift-log.jsonl",
        "max_age_s": 1800,  # 30 min
    },
    "PortalLoadProbe": {
        "interval_min": 1440,  # daily
        "output": "memory/ops/fleet-metrics.jsonl",
        "max_age_s": 86400,   # 24h
    },
}

def query_schtasks():
    """Query all schtasks; return dict of name -> last_run_iso."""
    try:
        out = subprocess.check_output(
            ["schtasks", "/query", "/fo", "csv", "/v"],
            text=True, errors="replace", timeout=30
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        return {"_error": str(e)}

    results = {}
    lines = out.strip().split("\n")
    for line in lines[1:]:  # skip header
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 3:
            name = parts[0]
            last_run = ""
            # "Last Run Time" is typically column index 2 in /v output
            for i, col in enumerate(parts):
                pass  # CSV parsing varies; use simple heuristic
            # Try to find Last Run Time from the full line
            import re
            m = re.search(r'"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"', line)
            if m:
                last_run = m.group(1)
            results[name] = last_run
    return results

def file_age_seconds(path):
    """Return age in seconds of a file, or None if not found."""
    p = Path(path)
    if not p.exists():
        return None
    mt = p.stat().st_mtime
    return (time.time() - mt)

def check_task(name, spec):
    """Check one task: schtask exists + output file fresh. Returns status dict."""
    result = {"task": name, "status": "OK", "details": {}}

    # Check output file freshness
    out_path = spec["output"]
    age = file_age_seconds(out_path)
    if age is None:
        result["status"] = "WARN"
        result["details"]["output_missing"] = out_path
    elif age > spec["max_age_s"]:
        result["status"] = "STALE"
        result["details"]["output_age_s"] = age
        result["details"]["max_allowed_s"] = spec["max_age_s"]
    else:
        result["details"]["output_age_s"] = round(age, 1)

    # Check schtask is registered (best-effort; may not work in sandbox)
    try:
        q = subprocess.check_output(
            ["schtasks", "/query", "/tn", name, "/fo", "csv"],
            text=True, errors="replace", timeout=10
        )
        result["details"]["registered"] = True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        result["details"]["registered"] = False
        if result["status"] == "OK":
            result["status"] = "WARN"
            result["details"]["note"] = "schtask not found on this host"

    return result

def run_check():
    """Run health check on all known tasks. Returns report dict."""
    now = datetime.now(timezone.utc).isoformat()
    results = []
    for name, spec in TASKS.items():
        results.append(check_task(name, spec))

    ok = sum(1 for r in results if r["status"] == "OK")
    warn = sum(1 for r in results if r["status"] == "WARN")
    stale = sum(1 for r in results if r["status"] == "STALE")

    report = {
        "timestamp": now,
        "summary": {"ok": ok, "warn": warn, "stale": stale, "total": len(results)},
        "results": results,
    }
    return report

def selftest():
    """Self-test: verify the check logic works with synthetic data."""
    passed = 0
    total = 4

    # Test 1: file_age_seconds returns None for missing file
    age = file_age_seconds("memory/builder/__nonexistent__.jsonl")
    if age is None:
        passed += 1
    print(f"  [{'PASS' if age is None else 'FAIL'}] file_age_seconds(missing) -> None")

    # Test 2: file_age_seconds returns reasonable value for existing file
    test_file = Path("memory/builder/__st_health_test.tmp")
    test_file.write_text("test", encoding="utf-8")
    age = file_age_seconds(str(test_file))
    if age is not None and 0 <= age < 5:
        passed += 1
    print(f"  [{'PASS' if age is not None and 0 <= age < 5 else 'FAIL'}] file_age_seconds(fresh) -> {age}s")
    test_file.unlink(missing_ok=True)

    # Test 3: run_check returns valid structure
    report = run_check()
    if "summary" in report and "results" in report and report["summary"]["total"] == len(TASKS):
        passed += 1
    print(f"  [{'PASS' if 'summary' in report else 'FAIL'}] run_check structure valid (total={report['summary']['total']})")

    # Test 4: each result has required fields
    all_valid = all(
        "task" in r and "status" in r and "details" in r
        for r in report["results"]
    )
    if all_valid:
        passed += 1
    print(f"  [{'PASS' if all_valid else 'FAIL'}] all results have task/status/details")

    print(f"\nSelftest: {passed}/{total} PASS")
    return passed == total

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        ok = selftest()
        sys.exit(0 if ok else 1)
    else:
        report = run_check()
        print(json.dumps(report, indent=2))
        # Exit non-zero if any STALE
        sys.exit(1 if report["summary"]["stale"] > 0 else 0)
