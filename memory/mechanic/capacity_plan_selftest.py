#!/usr/bin/env python3
"""capacity_plan_selftest.py - Self-test for capacity_plan.py (Goal #9)"""
import json, os, datetime, subprocess, sys, py_compile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "capacity_plan.py")
PASS = 0
FAIL = 0
results = []

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        results.append(f"  PASS: {name}")
    else:
        FAIL += 1
        results.append(f"  FAIL: {name} {detail}")

def run(args):
    return subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True, timeout=30)

print("=== capacity_plan.py Self-Test ===\n")

# Test 1: Script compiles
try:
    py_compile.compile(SCRIPT, doraise=True)
    check("py_compile", True)
except Exception as e:
    check("py_compile", False, str(e))

# Test 2: Run with real data
r = run(['--input', os.path.join(HERE, "..", "ops", "host_metrics.jsonl")])
check("run_real_data rc=0", r.returncode == 0, f"rc={r.returncode} stderr={r.stderr[:100]}")

# Test 3: Synthetic 7-day linear data - prediction accuracy
test_path = os.path.join(HERE, "_selftest_cap.jsonl")
base_ts = datetime.datetime(2026, 11, 15, 6, 0, 0)
growth = 1.43
entries = []
for day in range(7):
    ts = base_ts + datetime.timedelta(days=day)
    pct = 50.0 + (day * growth)
    entries.append({"host": "synth", "ts": ts.isoformat(),
                    "disk": {"total_gb": 500, "free_gb": 100, "pct_used": round(pct, 2)}})
with open(test_path, 'w') as f:
    for e in entries:
        f.write(json.dumps(e) + "\n")

r = run(['--input', test_path])
check("run_synth rc=0", r.returncode == 0, f"rc={r.returncode}")

with open(os.path.join(HERE, "capacity-plan-latest.json")) as f:
    jdata = json.load(f)
res = [x for x in jdata['results'] if x['host'] == 'synth' and x['metric'] == 'disk_pct'][0]
expected_days = (90 - entries[-1]['disk']['pct_used']) / growth
actual_days = res['days_to_breach']
error_pct = abs(actual_days - expected_days) / expected_days * 100 if actual_days else 999
check(f"prediction_accuracy ({actual_days}d vs {expected_days:.2f}d, err={error_pct:.1f}%)", error_pct < 10)

# Test 4: Alert fires within 48h window
alert_path = os.path.join(HERE, "_selftest_cap_alert.jsonl")
entries2 = []
for day in range(5):
    ts = datetime.datetime(2026, 11, 17, 6, 0) + datetime.timedelta(days=day)
    pct = 60.0 + day * 5.0
    entries2.append({"host": "alert", "ts": ts.isoformat(),
                     "disk": {"total_gb": 500, "free_gb": 100, "pct_used": pct}})
with open(alert_path, 'w') as f:
    for e in entries2:
        f.write(json.dumps(e) + "\n")

r = run(['--input', alert_path])
check("alert_fires rc=2", r.returncode == 2, f"rc={r.returncode}")
check("alert_in_stdout", "ALERT" in r.stdout, r.stdout[:100])

# Test 5: No alert when breach > 48h
safe_path = os.path.join(HERE, "_selftest_cap_safe.jsonl")
entries3 = []
for day in range(7):
    ts = datetime.datetime(2026, 11, 15, 6, 0) + datetime.timedelta(days=day)
    pct = 40.0 + day * 0.5
    entries3.append({"host": "safe", "ts": ts.isoformat(),
                     "disk": {"total_gb": 500, "free_gb": 100, "pct_used": pct}})
with open(safe_path, 'w') as f:
    for e in entries3:
        f.write(json.dumps(e) + "\n")

r = run(['--input', safe_path])
check("no_alert rc=0", r.returncode == 0, f"rc={r.returncode}")

# Test 6: Threshold is configurable
r = run(['--input', safe_path, '--threshold', '41'])
check("configurable_threshold rc!=0", r.returncode != 0, f"rc={r.returncode}")

# Test 7: Report file exists
report = os.path.join(HERE, "capacity-plan-2026-11-22.md")
check("report_exists", os.path.exists(report))
if os.path.exists(report):
    with open(report) as f:
        content = f.read()
    check("report_has_table", '|' in content and 'Host' in content)

# Cleanup
for p in [test_path, alert_path, safe_path]:
    if os.path.exists(p):
        os.remove(p)

print("\n".join(results))
print(f"\n=== {PASS}/{PASS+FAIL} PASS ===")
sys.exit(0 if FAIL == 0 else 1)
