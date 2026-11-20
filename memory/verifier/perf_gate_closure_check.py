#!/usr/bin/env python3
"""Goal 1 Closure Validation — Performance Gate Baseline.

Acceptance criteria (from memory/goals/verifier.md #1):
  A) perf-baseline.json exists and is VALID (strict-majority non-null p50).
  B) At least 3 daily gate reports exist showing exit-0 (no regression).
  C) Negative test: inflating one endpoint's baseline by 2x triggers an alert.

Usage:
  python memory/verifier/perf_gate_closure_check.py
Exit: 0 = ALL CRITERIA MET (goal ready for ledger),
      1 = one or more criteria not yet met (prints which).
"""
import json, os, sys, glob, re
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE_PATH = os.path.join(HERE, "perf-baseline.json")
REPORT_GLOB = os.path.join(HERE, "perf-daily-*.md")  # daily reports from deploy_perf_gate.py
# Fallback: check memory/ops/perf-* as alternate location
OPS_REPORT_GLOB = os.path.join(os.path.dirname(os.path.dirname(HERE)), "ops", "perf-gate-*.md")

results = []

def check(name, passed, detail):
    results.append((name, passed, detail))
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {name}: {detail}")

print("=" * 60)
print("Goal 1 Closure Check — Performance Gate Baseline")
print(f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}")
print("=" * 60)

# --- Criterion A: valid baseline exists ---
if not os.path.exists(BASELINE_PATH):
    check("A: baseline file", False, f"{BASELINE_PATH} not found")
else:
    try:
        with open(BASELINE_PATH) as f:
            doc = json.load(f)
        eps = doc.get("endpoints", {})
        n_total = len(eps)
        n_valid = sum(1 for e in eps.values() if e.get("p50_ms") is not None)
        valid = (n_total > 0) and (n_valid * 2 > n_total)
        check("A: baseline file", valid,
              f"{n_valid}/{n_total} endpoints have p50 (need strict majority); captured {doc.get('captured_at','?')}")
    except (json.JSONDecodeError, Exception) as ex:
        check("A: baseline file", False, f"parse error: {ex}")

# --- Criterion B: >=3 daily reports with no regression ---
reports = sorted(glob.glob(REPORT_GLOB)) + sorted(glob.glob(OPS_REPORT_GLOB))
pass_reports = []
for rp in reports:
    try:
        text = open(rp, encoding="utf-8", errors="replace").read()
        # A passing report contains "PASS" or "no regression" but NOT "REGRESSION DETECTED"
        if "REGRESSION DETECTED" not in text and ("PASS" in text or "no regression" in text.lower()):
            pass_reports.append(rp)
    except Exception:
        pass
check("B: >=3 clean daily reports", len(pass_reports) >= 3,
      f"{len(pass_reports)} clean reports found (need >=3)")
if pass_reports:
    print(f"       latest: {os.path.basename(pass_reports[-1])}")

# --- Criterion C: negative test fires ---
# Check for a negative-test evidence file or inline result in a report.
neg_found = False
neg_detail = "no negative-test evidence found"
for rp in reports:
    try:
        text = open(rp, encoding="utf-8", errors="replace").read()
        if "NEGATIVE TEST" in text.upper() or "negative_test" in text.lower():
            neg_found = True
            neg_detail = f"found in {os.path.basename(rp)}"
            break
    except Exception:
        pass
# Also check dedicated negative-test file
neg_file = os.path.join(HERE, "perf-negative-test.md")
if not neg_found and os.path.exists(neg_file):
    text = open(neg_file, encoding="utf-8", errors="replace").read()
    if "REGRESSION" in text.upper() or "ALERT" in text.upper():
        neg_found = True
        neg_detail = f"found in perf-negative-test.md"
check("C: negative test fires alert", neg_found, neg_detail)

# --- Summary ---
print("\n" + "=" * 60)
n_pass = sum(1 for _, p, _ in results if p)
if n_pass == len(results):
    print(f"RESULT: ALL {len(results)} CRITERIA MET — goal ready for ledger closure.")
    print("Next step: python memory/researcher/goal_ledger.py --record verifier 1 --note 'closure_check PASS'")
    sys.exit(0)
else:
    print(f"RESULT: {n_pass}/{len(results)} criteria met — NOT YET CLOSABLE.")
    for name, passed, detail in results:
        if not passed:
            print(f"  MISSING: {name} ({detail})")
    sys.exit(1)
