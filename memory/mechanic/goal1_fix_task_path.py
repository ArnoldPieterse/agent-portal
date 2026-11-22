#!/usr/bin/env python3
"""goal1_fix_task_path.py - One-shot fix for PortalLoadProbe silent-failure.

ROOT CAUSE: register_daily_probe.bat uses relative path `python memory\ops\load_probe.py`
which doesn't resolve in Task Scheduler's working directory context. Task registered
Nov 22 but no data written since Nov 20 (file mtime = 2026-11-20 09:00:03).

FIX: Re-register with absolute paths + explicit /create /d <workdir>, then trigger
one manual run to verify, then check --week-complete status.

USAGE (from non-sandbox White seat with schtasks COM available):
    python memory/mechanic/goal1_fix_task_path.py

Or step-by-step manually:
    1. schtasks /delete /tn PortalLoadProbe /f
    2. schtasks /create /tn PortalLoadProbe /tr "<PYTHON_EXE> <ABS_PATH_TO_LOAD_PROBE> --host 127.0.0.1 --port 8099" /sc daily /st 06:00 /f
    3. schtasks /run /tn PortalLoadProbe
    4. python memory/ops/load_trend.py --week-complete
"""
import os, sys, subprocess, json, shutil
from datetime import datetime

FLEET_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LOAD_PROBE = os.path.join(FLEET_ROOT, 'memory', 'ops', 'load_probe.py')
BASELINE_FILE = os.path.join(FLEET_ROOT, 'memory', 'ops', 'load-baseline.jsonl')
TASK_NAME = 'PortalLoadProbe'

# Detect python executable (the one that can actually run)
PYTHON_EXE = sys.executable or shutil.which('python')

print(f"[goal1-fix] Fleet root: {FLEET_ROOT}")
print(f"[goal1-fix] Python exe:  {PYTHON_EXE}")
print(f"[goal1-fix] Load probe:  {LOAD_PROBE}")
print(f"[goal1-fix] Baseline:    {BASELINE_FILE}")

# Step 0: Check current state
print("\n--- STEP 0: Current state ---")
if os.path.exists(BASELINE_FILE):
    mtime = os.path.getmtime(BASELINE_FILE)
    print(f"  Baseline last modified: {datetime.fromtimestamp(mtime)}")
    with open(BASELINE_FILE, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]
    dates = set()
    for l in lines:
        try:
            d = json.loads(l)
            if d.get('kind', 'latency') == 'latency' and isinstance(d.get('levels'), list):
                dates.add(d['ts'][:10])
        except (json.JSONDecodeError, ValueError):
            pass
    print(f"  Latency entries: {len(lines)}, unique dates: {sorted(dates)} ({len(dates)}/7)")
else:
    print("  Baseline file NOT FOUND")

# Step 1: Query existing task (informational - may fail if COM unavailable)
print("\n--- STEP 1: Query existing task ---")
r = subprocess.run(['schtasks', '/query', '/tn', TASK_NAME, '/fo', 'list'],
                   capture_output=True, text=True)
if r.returncode == 0:
    print(f"  Task exists. Output:\n{r.stdout[:500]}")
else:
    print(f"  schtasks query failed (rc={r.returncode}): {r.stderr.strip()[:200]}")
    print("  [NOTE] If COM is unavailable here, run this script from a seat where schtasks works.")
    sys.exit(1)

# Step 2: Delete and re-register with absolute path
print("\n--- STEP 2: Re-register with absolute paths ---")
subprocess.run(['schtasks', '/delete', '/tn', TASK_NAME, '/f'], capture_output=True, text=True)

tr_cmd = f'"{PYTHON_EXE}" "{LOAD_PROBE}" --host 127.0.0.1 --port 8099'
r = subprocess.run(['schtasks', '/create', '/tn', TASK_NAME, '/tr', tr_cmd,
                    '/sc', 'daily', '/st', '06:00', '/f'],
                   capture_output=True, text=True)
if r.returncode == 0:
    print(f"  [OK] Re-registered: {tr_cmd}")
else:
    print(f"  [FAIL] Re-register failed: {r.stderr.strip()[:200]}")
    sys.exit(1)

# Step 3: Trigger one manual run
print("\n--- STEP 3: Trigger manual run ---")
r = subprocess.run(['schtasks', '/run', '/tn', TASK_NAME], capture_output=True, text=True)
if r.returncode == 0:
    print("  [OK] Task triggered. Waiting 10s for completion...")
    import time; time.sleep(10)
else:
    print(f"  [WARN] Trigger failed: {r.stderr.strip()[:200]} (may still work if portal is up)")

# Step 4: Verify data was written
print("\n--- STEP 4: Verify new data ---")
if os.path.exists(BASELINE_FILE):
    with open(BASELINE_FILE, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]
    if lines:
        last = json.loads(lines[-1])
        print(f"  Last entry: ts={last.get('ts')} levels={len(last.get('levels', []))}")
else:
    print("  [WARN] Baseline file still not found")

# Step 5: Run week-complete check
print("\n--- STEP 5: Week-complete status ---")
r = subprocess.run([PYTHON_EXE, os.path.join(FLEET_ROOT, 'memory', 'ops', 'load_trend.py'), '--week-complete'],
                   capture_output=True, text=True, cwd=FLEET_ROOT)
print(f"  {r.stdout.strip()}")
if r.stderr.strip():
    print(f"  stderr: {r.stderr.strip()[:200]}")

print("\n[goal1-fix] Done. If week-complete shows 7/7, goal is ready for closure.")
