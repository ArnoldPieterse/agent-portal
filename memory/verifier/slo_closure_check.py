#!/usr/bin/env python3
"""slo_closure_check.py - Verifies goal #2 (SLO enforcement productionization) acceptance criteria.

Acceptance: two consecutive days of automated reports with no human intervention.
Run: python memory/verifier/slo_closure_check.py
Exit 0 = ready to close; exit 1 = not yet (prints what's missing).

Checks:
  1. slo-history.jsonl has >=2 consecutive dates with zero breaches
  2. Each date has a corresponding slo-report-YYYY-MM-DD.md file
  3. The report verdict line says PASS (not BREACH)
"""
import json, os, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORY = os.path.join(HERE, "slo-history.jsonl")
REPORT_DIR = HERE

def main():
    if not os.path.exists(HISTORY):
        print("FAIL: slo-history.jsonl does not exist yet. Task has not run.")
        sys.exit(1)
    
    entries = []
    with open(HISTORY, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    
    if len(entries) < 2:
        print(f"FAIL: only {len(entries)} run(s) recorded; need >=2 consecutive PASS days.")
        sys.exit(1)
    
    # Find longest streak of consecutive zero-breach dates
    dates = sorted(set(e["date"] for e in entries))
    no_breach_dates = set(e["date"] for e in entries if not e["breaches"])
    
    max_streak, cur_streak = 0, 0
    prev_date = None
    for d in dates:
        if d in no_breach_dates:
            if prev_date and (datetime.date.fromisoformat(d) - datetime.date.fromisoformat(prev_date)).days == 1:
                cur_streak += 1
            else:
                cur_streak = 1
            max_streak = max(max_streak, cur_streak)
        else:
            cur_streak = 0
        prev_date = d
    
    if max_streak < 2:
        print(f"FAIL: longest consecutive PASS streak = {max_streak} day(s); need >=2.")
        print(f"  Dates with no breach: {sorted(no_breach_dates)}")
        sys.exit(1)
    
    # Verify report files exist for the streak dates
    missing_reports = []
    for d in sorted(no_breach_dates):
        rep_path = os.path.join(REPORT_DIR, f"slo-report-{d}.md")
        if not os.path.exists(rep_path):
            missing_reports.append(d)
    
    if missing_reports:
        print(f"FAIL: report files missing for dates: {missing_reports}")
        sys.exit(1)
    
    # Verify verdict in reports says PASS
    bad_verdicts = []
    for d in sorted(no_breach_dates):
        rep_path = os.path.join(REPORT_DIR, f"slo-report-{d}.md")
        content = open(rep_path, "r", encoding="utf-8").read()
        if "PASS" not in content:
            bad_verdicts.append(d)
    
    if bad_verdicts:
        print(f"FAIL: reports without PASS verdict: {bad_verdicts}")
        sys.exit(1)
    
    print(f"OK: goal #2 acceptance met. {max_streak} consecutive PASS days confirmed.")
    print(f"  Close with: python memory/researcher/goal_ledger.py --record verifier 2 --note 'SLO task auto-ran {max_streak}d, all PASS'")
    sys.exit(0)

if __name__ == "__main__":
    main()
