#!/usr/bin/env python3
"""
Proactive Health Check - Mechanic Goal #1 (cycle-5)

Checks every 5 minutes:
  - Portal responding (HTTP 200 on :8099)
  - All 8 agents reachable (via /api/agents or process check)
  - Disk < 80%
  - Memory < 90%

Usage:
  python memory/mechanic/health_check.py --once       # single check, print results
  python memory/mechanic/health_check.py --schedule   # loop every 5 min (300s)
  python memory/mechanic/health_check.py --alert-test # simulate alert to verify wiring
"""
import json
import os
import sys
import time
import socket
import urllib.request
import urllib.error
import shutil
import platform
from datetime import datetime, timezone
from pathlib import Path

# --- Config ---
PORTAL_HOST = "127.0.0.1"
PORTAL_PORT = 8099
CHECK_INTERVAL_S = 300  # 5 minutes
DISK_THRESHOLD_PCT = 80
MEM_THRESHOLD_PCT = 90
LOG_FILE = Path(__file__).parent / "health_check.log"
ALERT_LOG = Path(__file__).parent / "health_alerts.jsonl"

# Expected agents (from agents.json)
EXPECTED_AGENTS = [
    "orchestrator", "researcher", "builder", "verifier",
    "designer", "archivist", "scribe", "mechanic"
]


def log(msg, level="INFO"):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"{ts} [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def alert(check_name, detail):
    """Write alert to JSONL log and attempt portal notification."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "check": check_name,
        "detail": detail,
        "severity": "CRITICAL",
    }
    try:
        with open(ALERT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as e:
        print(f"WARN: could not write alert log: {e}")
    # Attempt portal notification endpoint (best-effort)
    try:
        payload = json.dumps({"agent": "mechanic", "type": "health_alert", **entry}).encode()
        req = urllib.request.Request(
            f"http://{PORTAL_HOST}:{PORTAL_PORT}/api/notify",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except (urllib.error.URLError, OSError):
        pass  # portal may be down - that's what we're checking
    log(f"ALERT: {check_name}: {detail}", "CRITICAL")


def check_portal():
    """Check if portal is responding with HTTP 200."""
    try:
        req = urllib.request.Request(
            f"http://{PORTAL_HOST}:{PORTAL_PORT}/api/health",
            method="GET",
        )
        resp = urllib.request.urlopen(req, timeout=5)
        if resp.status == 200:
            return True, "HTTP 200"
        return False, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except (urllib.error.URLError, socket.timeout, OSError) as e:
        return False, f"unreachable: {e}"


def check_agents():
    """Check if all expected agents are listed by the portal."""
    try:
        req = urllib.request.Request(
            f"http://{PORTAL_HOST}:{PORTAL_PORT}/api/agents",
            method="GET",
        )
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode())
        # agents.json returns a list or dict
        if isinstance(data, list):
            found = {a.get("name", "") for a in data}
        elif isinstance(data, dict):
            found = set(data.keys())
        else:
            found = set()
        missing = [a for a in EXPECTED_AGENTS if a not in found]
        if missing:
            return False, f"missing agents: {missing}"
        return True, f"all {len(EXPECTED_AGENTS)} agents present"
    except (urllib.error.URLError, socket.timeout, OSError, json.JSONDecodeError) as e:
        return False, f"agent check failed: {e}"


def check_disk():
    """Check disk usage on the working drive (fallback to system drive)."""
    try:
        # Use current working directory's drive - works in sandbox
        cwd_drive = Path(os.getcwd()).resolve().anchor or "/"
        usage = shutil.disk_usage(cwd_drive)
        pct = round(usage.used / usage.total * 100, 1)
        if pct >= DISK_THRESHOLD_PCT:
            return False, f"disk at {pct}% (threshold {DISK_THRESHOLD_PCT}%)"
        return True, f"disk at {pct}%"
    except OSError:
        # Fallback: try common paths
        for candidate in ["/", "C:\\", os.path.expanduser("~")]:
            try:
                usage = shutil.disk_usage(candidate)
                pct = round(usage.used / usage.total * 100, 1)
                if pct >= DISK_THRESHOLD_PCT:
                    return False, f"disk at {pct}% (threshold {DISK_THRESHOLD_PCT}%)"
                return True, f"disk at {pct}%"
            except OSError:
                continue
        return False, "disk check: no accessible drive found"


def check_memory():
    """Check system memory usage. On Windows uses ctypes; fallback to /proc on Linux."""
    try:
        if platform.system() == "Windows":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            pct = stat.dwMemoryLoad
        else:
            with open("/proc/meminfo") as f:
                info = {}
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        info[parts[0].rstrip(":")] = int(parts[1])
                total = info.get("MemTotal", 1)
                avail = info.get("MemAvailable", 0)
                pct = round((total - avail) / total * 100, 1)
        if pct >= MEM_THRESHOLD_PCT:
            return False, f"memory at {pct}% (threshold {MEM_THRESHOLD_PCT}%)"
        return True, f"memory at {pct}%"
    except Exception as e:
        return False, f"memory check error: {e}"


def run_checks():
    """Run all health checks, return list of (name, ok, detail)."""
    results = []
    portal_ok, portal_detail = check_portal()
    results.append(("portal", portal_ok, portal_detail))

    if portal_ok:
        agents_ok, agents_detail = check_agents()
        results.append(("agents", agents_ok, agents_detail))
    else:
        results.append(("agents", False, "skipped (portal down)"))

    disk_ok, disk_detail = check_disk()
    results.append(("disk", disk_ok, disk_detail))

    mem_ok, mem_detail = check_memory()
    results.append(("memory", mem_ok, mem_detail))

    return results


def main():
    mode = "--once"
    if "--schedule" in sys.argv:
        mode = "--schedule"
    elif "--alert-test" in sys.argv:
        mode = "--alert-test"

    if mode == "--alert-test":
        log("ALERT-TEST: simulating a critical alert")
        alert("alert_test", "This is a test alert to verify wiring")
        print("Alert test complete. Check health_alerts.jsonl for the entry.")
        return 0

    if mode == "--once":
        results = run_checks()
        all_ok = True
        for name, ok, detail in results:
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {name}: {detail}")
            if not ok:
                all_ok = False
                alert(name, detail)
        print(f"\nOverall: {'HEALTHY' if all_ok else 'DEGRADED'}")
        return 0 if all_ok else 1

    # --schedule mode
    log(f"Health check scheduler started (interval={CHECK_INTERVAL_S}s)")
    while True:
        results = run_checks()
        ts = datetime.now(timezone.utc).isoformat()
        summary = {name: ("ok" if ok else "FAIL") for name, ok, _ in results}
        log(f"check complete: {summary}")
        for name, ok, detail in results:
            if not ok:
                alert(name, detail)
        time.sleep(CHECK_INTERVAL_S)


if __name__ == "__main__":
    sys.exit(main())
