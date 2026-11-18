#!/usr/bin/env python3
"""Goal #1 auto-closure: runs when load-baseline.jsonl has 7+ days.
Usage: python memory/mechanic/goal1_auto_close.py
Exits 0 + records ledger if complete; exits 1 with status if not yet.
"""
import json, os, subprocess, sys
from datetime import datetime

BASELINE = "memory/ops/load-baseline.jsonl"
TREND_PY = "memory/ops/load_trend.py"
LEDGER = "memory/researcher/goal_ledger.py"

def main():
    if not os.path.exists(BASELINE):
        print(f"[goal1] baseline not found: {BASELINE}")
        sys.exit(1)

    rows = [json.loads(l) for l in open(BASELINE) if l.strip()]
    days = len(set(r["ts"][:10] for r in rows))
    print(f"[goal1] {days}/7 days collected ({len(rows)} total rows)")

    if days < 7:
        oldest = min(r["ts"][:10] for r in rows)
        newest = max(r["ts"][:10] for r in rows)
        print(f"[goal1] range: {oldest} .. {newest}; need {7-days} more day(s)")
        sys.exit(1)

    # 7+ days: run week-complete analysis
    r = subprocess.run([sys.executable, TREND_PY, "--week-complete"], capture_output=True, text=True)
    print(f"[goal1] load_trend --week-complete rc={r.returncode}")
    if r.stdout: print(r.stdout[-500:])
    if r.stderr: print(r.stderr[-200:])

    if r.returncode == 0:
        # Record closure in ledger
        note = f"7/7 days load probe data + week-complete verdict PASS (ran {datetime.now().isoformat()})"
        subprocess.run([sys.executable, LEDGER, "--record", "mechanic", "1", "--note", note],
                       capture_output=True, text=True)
        print("[goal1] CLOSED - ledger recorded")
    else:
        print(f"[goal1] week-complete FAILED rc={r.returncode}")
        sys.exit(2)

if __name__ == "__main__":
    main()