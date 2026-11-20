"""
restart_portal.py - One-command portal restart with health check (Runbook step C)
Part of Mechanic Goal 10: Runbook Automation (top-5)

Usage: python memory/mechanic/restart_portal.py [--timeout 30]

Idempotent: if portal is already healthy, exits 0 without killing anything.
Logs to memory/mechanic/runbook-executions.jsonl. Runtime <60s.

Steps:
  1. Health-check :8099 (GET /api/health). If UP -> log NO-OP, exit 0.
  2. Find PID via _portal_pid.txt or netstat on :8099.
  3. Kill PID (taskkill /F).
  4. Trigger `schtasks /run /tn PortalRun` (elevated via elev.py if available,
     else direct schtasks - works when running as SYSTEM from a schtask context).
  5. Poll :8099 for up to --timeout seconds until healthy.
  6. Log result + new PID to runbook-executions.jsonl.
"""
import json, os, pathlib, subprocess, sys, time, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(HERE, "runbook-executions.jsonl")
PID_FILE = os.path.join(HERE, "..", "..", "_portal_pid.txt")  # relative to agent root
PORT = 8099
BASE = f"http://127.0.0.1:{PORT}"
DEFAULT_TIMEOUT = 30  # seconds to wait for portal to come back


def _log(entry: dict):
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    entry["script"] = "restart_portal.py"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def health_check(timeout=5):
    """Return (ok: bool, detail: str)."""
    try:
        with urllib.request.urlopen(BASE + "/api/health", timeout=timeout) as r:
            body = json.loads(r.read())
            return True, f"status={r.status} {body.get('state','?')}"
    except Exception as e:
        return False, str(e)[:120]


def find_pid():
    """Find portal PID from _portal_pid.txt or netstat."""
    # Try pid file first
    try:
        with open(PID_FILE, encoding="utf-8") as f:
            pid = int(f.read().strip())
            return pid, "pid_file"
    except (OSError, ValueError):
        pass
    # Fallback: netstat for :8099 listener
    try:
        out = subprocess.check_output(
            ["netstat", "-ano"], text=True, timeout=5
        )
        for line in out.splitlines():
            if f":{PORT} " in line and "LISTENING" in line:
                pid = int(line.strip().split()[-1])
                return pid, "netstat"
    except Exception:
        pass
    return None, "not_found"


def kill_pid(pid: int) -> bool:
    """Force-kill the process. Returns True on success."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True, timeout=10
        )
        return True
    except Exception:
        return False


def trigger_portal_task() -> bool:
    """Run the PortalRun scheduled task. Uses elev.py if available, else direct."""
    # Try elev.py first (sandbox-friendly)
    elev = os.path.join(os.path.dirname(HERE), "..", "elev.py")
    if os.path.isfile(elev):
        try:
            r = subprocess.run(
                [sys.executable, elev, "--shell", 'schtasks /run /tn PortalRun'],
                capture_output=True, text=True, timeout=15
            )
            if r.returncode == 0:
                return True
        except Exception:
            pass
    # Direct schtasks (works when running as SYSTEM/admin)
    try:
        r = subprocess.run(
            ["schtasks", "/run", "/tn", "PortalRun"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            return True
    except Exception:
        pass
    return False


def wait_healthy(timeout: float) -> tuple:
    """Poll health endpoint until OK or timeout. Returns (ok, elapsed_s)."""
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        ok, detail = health_check(timeout=3)
        if ok:
            return True, round(time.monotonic() - t0, 2)
        time.sleep(2)
    return False, round(time.monotonic() - t0, 2)


def main():
    timeout = DEFAULT_TIMEOUT
    if "--timeout" in sys.argv:
        idx = sys.argv.index("--timeout")
        try:
            timeout = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            pass

    t_start = time.monotonic()

    # Step 1: If already healthy -> NO-OP
    ok, detail = health_check(timeout=5)
    if ok:
        _log({"action": "noop", "reason": f"already healthy ({detail})",
              "total_seconds": round(time.monotonic() - t_start, 2)})
        print(f"NO-OP: portal already healthy ({detail})")
        return 0

    # Step 2: Find PID
    pid, source = find_pid()
    if pid:
        kill_pid(pid)
        time.sleep(2)  # let port release

    # Step 3: Trigger task
    triggered = trigger_portal_task()
    if not triggered:
        _log({"action": "FAIL", "reason": "could not trigger PortalRun task",
              "old_pid": pid, "total_seconds": round(time.monotonic() - t_start, 2)})
        print("FAIL: could not trigger PortalRun scheduled task")
        return 1

    # Step 4: Wait for health
    healthy, elapsed = wait_healthy(timeout)
    new_pid, _ = find_pid()

    result = {
        "action": "restart",
        "old_pid": pid,
        "pid_source": source,
        "new_pid": new_pid,
        "triggered": True,
        "healthy": healthy,
        "wait_seconds": elapsed,
        "total_seconds": round(time.monotonic() - t_start, 2),
        "within_budget": (time.monotonic() - t_start) < 60,
    }
    _log(result)

    if healthy:
        print(f"OK: portal restarted in {elapsed}s (new PID={new_pid})")
        return 0
    else:
        print(f"FAIL: portal not healthy after {elapsed}s wait")
        return 1


if __name__ == "__main__":
    sys.exit(main())