#!/usr/bin/env python3
"""goal1_one_command_close.py: One-command closure for Mechanic Goal #1 (Portal Load Test 7-Day).

Run on a NON-SANDBOX seat with :8099 egress (White ops terminal, or seated agent):
    python memory/mechanic/goal1_one_command_close.py

Steps:
  1. Run load_probe.py against 127.0.0.1:8099 (gets today's data point)
  2. Check distinct days in load-baseline.jsonl
  3. If >= 7 days: run load_week_complete.py for verdict
  4. If PASS: record ledger entry via goal_ledger.py --record mechanic 1
  5. Print final status

Exit codes: 0=goal closed, 1=verdict FAIL, 2=insufficient data (need more days)
"""
import json, os, subprocess, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.normpath(os.path.join(HERE, "..", "ops", "load-baseline.jsonl"))
PROBE = os.path.normpath(os.path.join(HERE, "..", "ops", "load_probe.py"))
WEEK_COMPLETE = os.path.join(HERE, "load_week_complete.py")
LEDGER = os.path.normpath(os.path.join(HERE, "..", "researcher", "goal_ledger.py"))

def run(cmd, timeout=120):
    print(f"  $ {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.stdout:
        for line in r.stdout.strip().splitlines()[:5]:
            print(f"    {line}")
    if r.stderr and r.returncode != 0:
        print(f"    [stderr] {r.stderr.strip()[:200]}")
    return r

def count_days():
    if not os.path.exists(BASELINE):
        return 0, []
    days = set()
    with open(BASELINE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "ts" in obj:
                days.add(obj["ts"][:10])
    return len(days), sorted(days)

def main():
    print("=" * 60)
    print(f"Goal #1 One-Command Close: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Run the load probe to get today's data point
    print("\n[1/4] Running load probe against 127.0.0.1:8099...")
    r = run([sys.executable, PROBE, "--host", "127.0.0.1", "--port", "8099"], timeout=180)
    if "OUTAGE" in (r.stdout or ""):
        print("  WARNING: probe reported OUTAGE - portal may be down. Continuing with existing data.")

    # Step 2: Check day count
    print("\n[2/4] Checking distinct days in load-baseline.jsonl...")
    n, days = count_days()
    print(f"  Days: {n}/7 -> {days}")

    if n < 7:
        missing = 7 - n
        print(f"\n  INSUFFICIENT DATA: need {missing} more day(s).")
        print("  The PortalLoadProbe schtask accumulates data daily at 06:00.")
        print("  Re-run this script after enough days have passed.")
        sys.exit(2)

    # Step 3: Run week-complete verdict
    print("\n[3/4] Running week-complete verdict...")
    r = run([sys.executable, WEEK_COMPLETE], timeout=60)
    if r.returncode == 0:
        verdict_str = "PASS"
    elif r.returncode == 1:
        verdict_str = "FAIL"
    else:
        print(f"  Unexpected exit code: {r.returncode}")
        sys.exit(r.returncode)

    # Step 4: Record ledger if PASS
    print(f"\n[4/4] Verdict: {verdict_str}")
    if verdict_str == "PASS":
        note = f"7-day load test PASS; days={days}; report=memory/mechanic/load-test-week.md"
        r = run([sys.executable, LEDGER, "--record", "mechanic", "1", "--note", note], timeout=30)
        print(f"\n  *** GOAL #1 CLOSED (PASS) ***")
    else:
        print("\n  Verdict is FAIL - see report for details. Not recording closure.")
        sys.exit(1)

if __name__ == "__main__":
    main()
