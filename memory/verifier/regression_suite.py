#!/usr/bin/env python3
"""Continuous Regression Suite - Verifier Goal #1 (cycle-7)

Runs all existing test scripts in sequence; produces a single pass/fail report
with per-suite timing.

Usage:
    python memory/verifier/regression_suite.py --full      # all suites
    python memory/verifier/regression_suite.py --static    # no external services
    python memory/verifier/regression_suite.py --suite smoke8  # single suite

Exit codes:
  0 = all suites pass
  1 = one or more suites fail
  2 = no suites could run (all skipped)
"""
import argparse, json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VERIFIER_DIR = Path(__file__).resolve().parent
REPORT_PATH = VERIFIER_DIR / "regression-suite-report.json"

# Suite definitions: (name, script, args, requires_live)
SUITES = [
    {"id": "smoke8", "script": "smoke8.py", "args": ["--static"], "live_args": ["--static"], "requires_live": False},
    {"id": "contract_test", "script": "contract_test.py", "args": [], "requires_live": True},
    {"id": "hotload_test", "script": "hotload_test.py", "args": ["--suite", "all"], "requires_live": True},
    {"id": "wedge_regression", "script": "test_wedge_regression.py", "args": [], "requires_live": True},
    {"id": "verify_endpoints", "script": "verify_endpoints.py", "args": [], "requires_live": True},
]


def is_port_reachable(port=8099, timeout=2):
    """Quick TCP check if portal is up."""
    import socket
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        s.close()
        return True
    except (OSError, ConnectionRefusedError):
        return False


def is_studio_reachable(port=8888, timeout=2):
    """Quick TCP check if Studio is up."""
    import socket
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        s.close()
        return True
    except (OSError, ConnectionRefusedError):
        return False


def run_suite(suite: dict, live: bool) -> dict:
    """Run a single test suite; return result dict."""
    script_path = VERIFIER_DIR / suite["script"]
    if not script_path.exists():
        return {"id": suite["id"], "status": "SKIP", "reason": f"{suite['script']} not found", "duration_s": 0}

    # Determine args
    if live and "live_args" in suite:
        args = [sys.executable, str(script_path)] + suite["live_args"]
    else:
        args = [sys.executable, str(script_path)] + suite["args"]

    # Gate on external services
    if live and suite.get("requires_live"):
        if not is_port_reachable(8099):
            return {"id": suite["id"], "status": "SKIP", "reason": "portal :8099 unreachable", "duration_s": 0}
        if suite["id"] == "hotload_test" and not is_studio_reachable(8888):
            return {"id": suite["id"], "status": "SKIP", "reason": "studio :8888 unreachable", "duration_s": 0}
    elif not live and suite.get("requires_live"):
        return {"id": suite["id"], "status": "SKIP", "reason": "--static mode; live service required", "duration_s": 0}

    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            args, capture_output=True, text=True,
            timeout=55, cwd=str(ROOT)
        )
        duration = round(time.monotonic() - t0, 2)
        status = "PASS" if proc.returncode == 0 else "FAIL"
        return {
            "id": suite["id"],
            "status": status,
            "exit_code": proc.returncode,
            "duration_s": duration,
            "stdout_tail": proc.stdout[-500:] if proc.stdout else "",
            "stderr_tail": proc.stderr[-300:] if proc.stderr and status == "FAIL" else "",
        }
    except subprocess.TimeoutExpired:
        duration = round(time.monotonic() - t0, 2)
        return {"id": suite["id"], "status": "TIMEOUT", "exit_code": -1, "duration_s": duration,
                "stderr_tail": f"exceeded 55s limit"}
    except Exception as e:
        duration = round(time.monotonic() - t0, 2)
        return {"id": suite["id"], "status": "ERROR", "exit_code": -1, "duration_s": duration,
                "stderr_tail": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Continuous Regression Suite")
    parser.add_argument("--full", action="store_true", help="Run all suites (live)")
    parser.add_argument("--static", action="store_true", help="Run only static suites")
    parser.add_argument("--suite", type=str, help="Run a single suite by id")
    args = parser.parse_args()

    live = args.full  # --full implies live
    if args.suite:
        suites_to_run = [s for s in SUITES if s["id"] == args.suite]
        if not suites_to_run:
            print(f"ERROR: unknown suite '{args.suite}'. Available: {[s['id'] for s in SUITES]}")
            sys.exit(2)
    else:
        # In static mode, only run non-live suites
        if args.static or not live:
            suites_to_run = [s for s in SUITES if not s["requires_live"]]
        else:
            suites_to_run = list(SUITES)

    results = []
    total_t0 = time.monotonic()

    print(f"\n{'='*60}")
    print(f"  REGRESSION SUITE - {datetime.now(timezone.utc).isoformat()[:19]}Z")
    print(f"  Mode: {'LIVE' if live else 'STATIC'} | Suites: {len(suites_to_run)}")
    print(f"{'='*60}\n")

    for suite in suites_to_run:
        result = run_suite(suite, live)
        results.append(result)
        icon = {"PASS": "\u2705", "FAIL": "\u274c", "SKIP": "\u23ed\ufe0f", "TIMEOUT": "\u23f1", "ERROR": "\u26a0\ufe0f"}.get(result["status"], "?")
        print(f"  {icon} {result['id']:<20} {result['status']:<8} {result['duration_s']:>6.2f}s")
        if result["status"] in ("FAIL", "TIMEOUT", "ERROR"):
            tail = result.get("stderr_tail", "") or result.get("stdout_tail", "")
            for line in tail.strip().splitlines()[-3:]:
                print(f"       | {line}")

    total_duration = round(time.monotonic() - total_t0, 2)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] in ("FAIL", "TIMEOUT", "ERROR"))
    skipped = sum(1 for r in results if r["status"] == "SKIP")

    overall = "PASS" if failed == 0 and passed > 0 else ("FAIL" if failed > 0 else "NO_TESTS_RAN")

    print(f"\n{'='*60}")
    print(f"  RESULT: {overall} | {passed} pass, {failed} fail, {skipped} skip | total {total_duration}s")
    print(f"{'='*60}\n")

    # Write report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "live" if live else "static",
        "overall": overall,
        "total_duration_s": total_duration,
        "summary": {"pass": passed, "fail": failed, "skip": skipped},
        "suites": results,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(f"  Report: {REPORT_PATH.relative_to(ROOT)}")

    if overall == "NO_TESTS_RAN":
        sys.exit(2)
    elif overall == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
