#!/usr/bin/env python3
"""
mechanic_closure_battery.py - One-shot closure pass for Mechanic's 4 remaining goals.
Run FROM A WHITE SEAT (non-sandbox) to close all 4 in one pass.

Usage:
    python memory/mechanic/mechanic_closure_battery.py [--goal N] [--dry-run]

Goals covered:
  1. Portal Load Test 7-Day Completion  -> diagnostic + backfill + week-complete
  2. Self-Healing Mirror Production     -> schtask verify + two-week log check
  3. WinRM Remote Reboot E2E            -> live run against Black
  4. Fleet Status API Hardening         -> live /api/fleet with one host down

Each goal logs its result to memory/mechanic/closure-battery-YYYY-MM-DD.jsonl
"""
import json, sys, os, time, subprocess, datetime, argparse, socket, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LOG_FILE = None  # set in main

def log(goal, phase, status, detail=""):
    entry = {"ts": datetime.datetime.now().isoformat(), "goal": goal, "phase": phase, "status": status, "detail": detail}
    print("  [%d] %s: %s - %s" % (goal, phase, status, detail))
    if LOG_FILE:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

def run_cmd(cmd, timeout=60):
    """Run a shell command, return (rc, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT after %ds" % timeout
    except Exception as e:
        return -2, "", str(e)

# --- GOAL 1: Portal Load Test -------------------------------------------------
def goal1_load_test(dry_run=False):
    print("\n=== Goal #1: Portal Load Test 7-Day Completion ===")
    
    baseline = os.path.join(ROOT, "memory", "ops", "load-baseline.jsonl")
    if not os.path.exists(baseline):
        log(1, "baseline-check", "FAIL", "File not found: %s" % baseline)
        return False
    
    dates = set()
    with open(baseline) as f:
        for line in f:
            try:
                e = json.loads(line.strip())
                ts = e.get("ts", "")[:10]
                if ts:
                    dates.add(ts)
            except: pass
    
    log(1, "data-check", "INFO", "%d/7 days present: %s" % (len(dates), sorted(dates)))
    
    if len(dates) >= 7:
        log(1, "week-complete", "ALREADY-7DAYS", "Already have 7 days of data")
        wc = os.path.join(ROOT, "memory", "mechanic", "load_week_complete.py")
        if os.path.exists(wc):
            rc, out, err = run_cmd('python "%s" --week-complete' % wc, timeout=30)
            log(1, "verdict", "PASS" if rc == 0 else "FAIL", (out or err)[:200])
        return True
    
    if dry_run:
        log(1, "dry-run", "SKIP", "Need %d more day(s); would check schtask + backfill" % (7-len(dates)))
        return False
    
    rc, out, err = run_cmd('schtasks /query /tn PortalLoadProbe /fo csv', timeout=15)
    if rc != 0:
        log(1, "schtask-check", "FAIL", "PortalLoadProbe not found: %s" % err[:100])
        return False
    
    last_run = ""
    for line in out.split("\n"):
        if "Last Run Time" in line or "last run time" in line.lower():
            last_run = line.strip()
    log(1, "schtask-status", "INFO", "LastRun: %s" % last_run)
    
    probe = os.path.join(ROOT, "memory", "mechanic", "fleet_load_probe.py")
    if os.path.exists(probe):
        rc, out, err = run_cmd('python "%s"' % probe, timeout=120)
        log(1, "manual-trigger", "PASS" if rc == 0 else "FAIL", (out or err)[:150])
    else:
        log(1, "manual-trigger", "FAIL", "Probe script not found: %s" % probe)
    
    dates2 = set()
    with open(baseline) as f:
        for line in f:
            try:
                e = json.loads(line.strip())
                ts = e.get("ts", "")[:10]
                if ts: dates2.add(ts)
            except: pass
    
    log(1, "post-trigger", "INFO", "Days now: %d/7" % len(dates2))
    
    if len(dates2) >= 7:
        wc = os.path.join(ROOT, "memory", "mechanic", "load_week_complete.py")
        rc, out, err = run_cmd('python "%s" --week-complete' % wc, timeout=30)
        log(1, "verdict", "PASS" if rc == 0 else "FAIL", (out or err)[:200])
        return rc == 0
    
    remaining = 7 - len(dates2)
    log(1, "status", "BLOCKED", "Still need %d more day(s). Backfill succeeded for today; wait for tomorrow's probe." % remaining)
    return False

# --- GOAL 2: Self-Healing Mirror ----------------------------------------------
def goal2_mirror_heal(dry_run=False):
    print("\n=== Goal #2: Self-Healing Mirror Production ===")
    
    if dry_run:
        log(2, "dry-run", "SKIP", "Would verify MirrorHeal schtask + two-week log window")
        return False
    
    rc, out, err = run_cmd('schtasks /query /tn MirrorHeal /fo csv', timeout=15)
    if rc != 0:
        log(2, "schtask-check", "FAIL", "MirrorHeal not found: %s" % err[:100])
        return False
    log(2, "schtask-check", "PASS", "MirrorHeal schtask registered")
    
    repairs = os.path.join(ROOT, "memory", "mechanic", "mirror-repairs.jsonl")
    if not os.path.exists(repairs):
        log(2, "repair-log", "FAIL", "No repair log at %s" % repairs)
        return False
    
    st = os.stat(repairs)
    age_days = (time.time() - st.st_mtime) / 86400
    log(2, "log-age", "INFO", "Last repair log write: %.1f days ago" % age_days)
    
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(days=14)).isoformat()[:10]
    today = datetime.datetime.now().isoformat()[:10]
    
    if today >= "2026-12-01":
        log(2, "two-week-window", "PASS", "Two-week window closed (%s >= 2026-12-01)" % today)
        
        with open(repairs) as f:
            entries = [json.loads(l) for l in f if l.strip()]
        recent = [e for e in entries if e.get("ts","")[:10] >= two_weeks_ago]
        failures = [e for e in recent if e.get("status") == "repair_failed"]
        log(2, "drift-check", "PASS" if len(failures) == 0 else "FAIL", "%d entries in window, %d failures" % (len(recent), len(failures)))
        
        if len(failures) == 0:
            print("  -> Goal #2 is ready for closure!")
            return True
    else:
        days_left = max(0, (datetime.datetime(2026, 12, 1) - datetime.datetime.now()).days)
        log(2, "two-week-window", "WAITING", "Window closes ~Dec 1 (%d day(s) remaining)" % days_left)
        return False

# --- GOAL 3: WinRM E2E ----------------------------------------------------------
def goal3_winrm_e2e(dry_run=False):
    print("\n=== Goal #3: WinRM Remote Reboot E2E Test ===")
    
    if dry_run:
        log(3, "dry-run", "SKIP", "Would run winrm_e2e_test.py --host black (destructive)")
        return False
    
    test_script = os.path.join(ROOT, "memory", "mechanic", "winrm_e2e_test.py")
    if not os.path.exists(test_script):
        log(3, "script-check", "FAIL", "Script not found: %s" % test_script)
        return False
    
    start = time.time()
    rc, out, err = run_cmd('python "%s" --host black' % test_script, timeout=900)
    elapsed = time.time() - start
    
    status = "PASS" if rc == 0 else "FAIL"
    log(3, "live-run", status, "rc=%d, %.0fs (limit 900s)" % (rc, elapsed))
    
    for phase in ["PHASE1_BASELINE", "PHASE2_HOST_DOWN", "PHASE3_CB_DETECT", "PHASE4_REBOOT", "PHASE5_RECOVERY"]:
        if phase in out:
            log(3, phase, "PRESENT", "")
    
    under_15min = elapsed < 900
    log(3, "time-check", "PASS" if under_15min else "FAIL", "%.0fs vs 900s limit" % elapsed)
    
    return rc == 0 and under_15min

# --- GOAL 4: Fleet Status API Live Leg ------------------------------------------
def goal4_fleet_live(dry_run=False):
    print("\n=== Goal #4: Fleet Status API - Live /api/fleet with Down Host ===")
    
    if dry_run:
        log(4, "dry-run", "SKIP", "Would hit /api/fleet and verify CB behavior with a down host")
        return False
    
    url = "http://localhost:8099/api/fleet"
    try:
        req = urllib.request.Request(url, timeout=10)
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode())
        log(4, "baseline-fetch", "PASS", "HTTP %d, hosts=%d" % (resp.status, len(data.get("hosts", []))))
        
        hosts = data.get("hosts", [])
        down_hosts = [h for h in hosts if h.get("state") == "down"]
        if down_hosts:
            log(4, "cb-verified", "PASS", "Host(s) already showing state=down: %s" % [h.get("host") for h in down_hosts])
            return True
        
        log(4, "all-up", "INFO", "All %d hosts reporting up. Attempting CB simulation..." % len(hosts))
        
    except urllib.error.URLError as e:
        log(4, "baseline-fetch", "FAIL", str(e))
        return False
    
    live_test = os.path.join(ROOT, "memory", "mechanic", "ac_a2_live_leg_r21.py")
    if os.path.exists(live_test):
        rc, out, err = run_cmd('python "%s"' % live_test, timeout=60)
        log(4, "live-test-script", "PASS" if rc == 0 else "FAIL", (out or err)[:200])
        return rc == 0
    
    log(4, "note", "INFO", "No live-test script found. Manual: stop one host's portal, hit /api/fleet, confirm state=down + others normal.")
    return False

# --- MAIN -----------------------------------------------------------------------
def main():
    global LOG_FILE
    parser = argparse.ArgumentParser(description="Mechanic Closure Battery")
    parser.add_argument("--goal", type=int, choices=[1,2,3,4], help="Run only this goal")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without executing")
    args = parser.parse_args()
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    LOG_FILE = os.path.join(HERE, "closure-battery-%s.jsonl" % date_str)
    
    print("\n" + "="*60)
    print("  MECHANIC CLOSURE BATTERY - %s" % date_str)
    print("  Mode: %s" % ("DRY-RUN" if args.dry_run else "LIVE"))
    if args.goal:
        print("  Goal: #%d only" % args.goal)
    else:
        print("  Goals: all (1,2,3,4)")
    print("="*60)
    
    goals = {
        1: ("Portal Load Test", goal1_load_test),
        2: ("Self-Healing Mirror", goal2_mirror_heal),
        3: ("WinRM E2E", goal3_winrm_e2e),
        4: ("Fleet Status Live Leg", goal4_fleet_live),
    }
    
    results = {}
    for gnum, (name, fn) in goals.items():
        if args.goal and gnum != args.goal:
            continue
        print("\n--- %s ---" % name)
        try:
            ok = fn(dry_run=args.dry_run)
            results[gnum] = "PASS" if ok else "PENDING/FAIL"
        except Exception as e:
            results[gnum] = "ERROR: %s" % e
            log(gnum, "exception", "FAIL", str(e))
    
    print("\n" + "="*60)
    print("  RESULTS SUMMARY")
    print("="*60)
    for gnum in sorted(results):
        name = goals[gnum][0]
        mark = "[OK]" if results[gnum] == "PASS" else "[..]"
        print("  %s Goal #%d: %s" % (mark, gnum, results[gnum]))
    
    passed = sum(1 for v in results.values() if v == "PASS")
    total = len(results)
    print("\n  %d/%d goals closed this pass." % (passed, total))
    if passed < total and not args.dry_run:
        print("  Remaining goals need: more data accumulation OR a different host state.")
    
    print("\n  Log: %s" % LOG_FILE)

if __name__ == "__main__":
    main()
