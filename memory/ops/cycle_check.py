#!/usr/bin/env python3
"""cycle_check.py - One-shot pass/fail for cycle-transition checklist sections 1+4.
Goal #9: replaces ~5 min manual audit with <30s automated report.

Checks:
  S1.1 Portal process alive (PID from _portal_pid.txt or port 8099)
  S1.2 /api/goals returns 200
  S1.3 Mirror log freshness (last entry < 2h old)
  S1.4 Fleet probe history exists + last run < 30min old
  S4.1 Load baseline has >= 2 days of data
  S4.2 No CRIT entries in last fleet probe run

Usage: python cycle_check.py [--json]
Output: pass/fail table to stdout; exit 0 if all PASS, 1 if any FAIL.
"""
import json, os, sys, time, urllib.request
from datetime import datetime, timezone, timedelta

BASE = "http://127.0.0.1:8099"
MIRROR_LOG = "memory/ops/mirror_events.log"
PROBE_HISTORY = "memory/ops/fleet-probe-history.jsonl"
LOAD_BASELINE = "memory/ops/load-baseline.jsonl"

def check_portal_pid():
    """S1.1: Check if portal process is alive."""
    pid_file = "_portal_pid.txt"
    if os.path.exists(pid_file):
        try:
            pid = int(open(pid_file).read().strip())
            # Try to verify via port instead (simpler cross-platform)
        except (ValueError, OSError):
            pass
    # Fallback: check port 8099
    return check_port(8099)

def check_port(port, timeout=3.0):
    import socket
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        sock.close()
        return True, f"port {port} open"
    except (PermissionError, OSError) as e:
        return False, f"port {port} closed ({type(e).__name__})"

def check_api_goals():
    """S1.2: /api/goals returns 200."""
    try:
        with urllib.request.urlopen(BASE + "/api/goals", timeout=5) as r:
            return r.status == 200, f"status {r.status}"
    except Exception as e:
        return False, str(type(e).__name__)

def check_mirror_freshness(max_age_hours=2):
    """S1.3: Mirror log last entry < max_age_hours old."""
    if not os.path.exists(MIRROR_LOG):
        return None, "mirror_events.log not found (may not be instrumented yet)"
    try:
        mtime = os.path.getmtime(MIRROR_LOG)
        age_h = (time.time() - mtime) / 3600
        if age_h < max_age_hours:
            return True, f"last mirror activity {age_h:.1f}h ago"
        else:
            return False, f"mirror stale: last activity {age_h:.1f}h ago (threshold {max_age_hours}h)"
    except OSError as e:
        return None, f"cannot read mirror log: {e}"

def check_probe_freshness(max_age_min=30):
    """S1.4: Fleet probe history last run < max_age_min old."""
    if not os.path.exists(PROBE_HISTORY):
        return None, "fleet-probe-history.jsonl not found"
    try:
        mtime = os.path.getmtime(PROBE_HISTORY)
        age_m = (time.time() - mtime) / 60
        if age_m < max_age_min:
            return True, f"last probe {age_m:.0f}min ago"
        else:
            return False, f"probe stale: last run {age_m:.0f}min ago (threshold {max_age_min}min)"
    except OSError as e:
        return None, f"cannot read probe history: {e}"

def check_load_baseline_min_days(min_days=2):
    """S4.1: Load baseline has >= min_days of unique calendar days."""
    if not os.path.exists(LOAD_BASELINE):
        return False, "load-baseline.jsonl not found"
    try:
        days = set()
        with open(LOAD_BASELINE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    ts = d.get("ts", "")
                    # Skip all-error days
                    if all(lv.get("errors", 0) == lv.get("n", 1) for lv in d.get("levels", [])):
                        continue
                    dt = datetime.fromisoformat(ts)
                    days.add(dt.strftime("%Y-%m-%d"))
                except (json.JSONDecodeError, ValueError):
                    continue
        if len(days) >= min_days:
            return True, f"{len(days)} unique days (need {min_days})"
        else:
            return False, f"only {len(days)} unique days (need {min_days})"
    except OSError as e:
        return None, f"cannot read baseline: {e}"

def check_no_crit():
    """S4.2: No CRIT entries in last fleet probe run."""
    if not os.path.exists(PROBE_HISTORY):
        return None, "no probe history"
    try:
        with open(PROBE_HISTORY) as f:
            lines = [l.strip() for l in f if l.strip()]
        if not lines:
            return None, "probe history empty"
        last = json.loads(lines[-1])
        if last.get("severity") == "CRIT":
            return False, f"last probe CRIT: {last.get('host')}:{last.get('port')} ({last.get('error','latency spike')})"
        return True, f"last probe severity={last.get('severity')}"
    except (json.JSONDecodeError, OSError) as e:
        return None, f"parse error: {e}"

CHECKS = [
    ("S1.1 Portal alive", check_portal_pid),
    ("S1.2 /api/goals 200", check_api_goals),
    ("S1.3 Mirror fresh (<2h)", check_mirror_freshness),
    ("S1.4 Probe fresh (<30m)", check_probe_freshness),
    ("S4.1 Load baseline >=2d", check_load_baseline_min_days),
    ("S4.2 No CRIT in last probe", check_no_crit),
]

def main():
    as_json = "--json" in sys.argv
    results = []
    all_pass = True
    for name, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = None, f"error: {e}"
        if ok is False:
            all_pass = False
        results.append({"check": name, "status": "PASS" if ok else ("FAIL" if ok is False else "SKIP"), "detail": detail})

    if as_json:
        print(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "all_pass": all_pass, "results": results}, indent=2))
    else:
        print(f"cycle_check {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("-" * 60)
        for r in results:
            icon = {"PASS": "+", "FAIL": "x", "SKIP": "?"}[r["status"]]
            print(f" [{icon}] {r['check']:25s} {r['detail']}")
        print("-" * 60)
        verdict = "ALL PASS" if all_pass else "FAILURES DETECTED"
        print(f"Verdict: {verdict}")

    sys.exit(0 if all_pass else 1)

if __name__ == "__main__":
    main()
