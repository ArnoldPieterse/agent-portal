#!/usr/bin/env python3
"""goal4_closure.py - one-shot closure for Mechanic goal #4 (portal load baseline).
Prerequisite: 7 unique days of data in load-baseline.jsonl.
Run: python memory/ops/goal4_closure.py
Steps: validate data -> run trend --week-complete -> record in ledger -> print verdict."""
import json, os, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "load-baseline.jsonl")
TREND = os.path.join(HERE, "load_trend.py")
LEDGER = os.path.join(HERE, "..", "researcher", "goal_ledger.py")

def main():
    # 1. Validate: need >=7 unique dates
    rows = []
    with open(BASELINE) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    dates = sorted(set(r["ts"].split(" ")[0] for r in rows))
    print(f"[1/3] Baseline validation: {len(dates)}/7 unique days -> {dates[0]} .. {dates[-1]}")
    if len(dates) < 7:
        print(f"FAIL: need 7 days, have {len(dates)}. Wait for more probes.")
        sys.exit(1)

    # Check structural integrity
    for r in rows:
        for lv in r["levels"]:
            if "skipped" in lv or not all(k in lv for k in ("p50_ms","p95_ms","p99_ms")):
                print(f"FAIL: bad row at {r['ts']}: {lv}")
                sys.exit(1)
    print("  All rows structurally valid.")

    # 2. Run trend --week-complete
    print("[2/3] Running load_trend.py --week-complete ...")
    r = subprocess.run([sys.executable, TREND, "--week-complete"], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(f"FAIL: trend exited {r.returncode}")
        print(r.stderr)
        sys.exit(1)

    # 3. Record in ledger
    note = f"goal4_closure.py run {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}: 7-day baseline validated, week-complete PASS, artifact=memory/ops/load-baseline.jsonl"
    print(f"[3/3] Recording in goal_ledger: mechanic #4")
    r2 = subprocess.run([sys.executable, LEDGER, "--record", "mechanic", "4", "--note", note],
                        capture_output=True, text=True)
    print(r2.stdout.strip())
    if r2.returncode != 0:
        print(f"WARN: ledger exited {r2.returncode}: {r2.stderr}")
    else:
        print("\nGATE #4 CLOSED. Verdict: PASS (7-day baseline complete, regression demo ready).")

if __name__ == "__main__":
    main()
