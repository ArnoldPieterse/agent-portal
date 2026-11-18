#!/usr/bin/env python3
"""
Auto-Restart Runbook - Mechanic Goal #2

Detects portal down, attempts restart up to 3 times with 10s intervals.
If still down after 3 attempts, logs NEEDS-HUMAN with diagnostics.

Usage:
  python memory/mechanic/auto_restart.py          # one-shot check + restart if needed
  python memory/mechanic/auto_restart.py --test   # simulate: pretend portal is down
"""
import subprocess, time, socket, os, json, sys, signal
from datetime import datetime
from pathlib import Path

PORTAL_PORT = 8099
PORTAL_SCRIPT = "agent_portal.py"
MAX_ATTEMPTS = 3
RESTART_WAIT_S = 10
LOG_FILE = Path("memory/mechanic/auto_restart.log.jsonl")
BLOCKERS_FILE = Path("memory/ops/blockers.md")


def ts():
    return datetime.now().isoformat(timespec="seconds")


def log_event(event: str, **kwargs):
    """Append a structured event to the JSONL log."""
    entry = {"ts": ts(), "event": event, **kwargs}
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[{entry['ts']}] {event}: {kwargs}")


def is_portal_up(port: int = PORTAL_PORT) -> bool:
    """Check if portal is listening on its port."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=3):
            return True
    except (ConnectionRefusedError, OSError):
        return False


def find_portal_pid() -> int | None:
    """Find PID of agent_portal.py process."""
    try:
        result = subprocess.run(
            ["python", "-c",
             "import subprocess; r=subprocess.run(['wmic','process','where',\"'name like \'%python%\' and commandline like '%agent_portal%'\"],capture_output=True,text=True); lines=[l for l in r.stdout.split('\n') if 'agent_portal' in l]; print(lines[0].split()[-1] if lines else '')"],
            capture_output=True, text=True, timeout=10
        )
        pid_str = result.stdout.strip()
        return int(pid_str) if pid_str.isdigit() else None
    except Exception:
        return None


def get_diagnostics() -> dict:
    """Collect diagnostics for NEEDS-HUMAN escalation."""
    diags = {
        "timestamp": ts(),
        "portal_port": PORTAL_PORT,
        "portal_up": is_portal_up(),
        "portal_pid": find_portal_pid(),
    }
    # Disk space
    try:
        usage = os.statvfs(".") if hasattr(os, 'statvfs') else None
        if usage:
            diags["disk_free_mb"] = int(usage.f_bavail * usage.f_frsize / 1024 / 1024)
    except Exception:
        pass
    # Last few lines of health check log
    try:
        hc_log = Path("memory/mechanic/health_check.log")
        if hc_log.exists():
            lines = hc_log.read_text().strip().split("\n")
            diags["recent_health_log"] = lines[-3:]
    except Exception:
        pass
    return diags


def attempt_restart() -> bool:
    """Try to start agent_portal.py in background. Returns True if process launched."""
    try:
        # Use subprocess with DETACHED_PROCESS on Windows
        creationflags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen(
            [sys.executable, PORTAL_SCRIPT],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
            cwd=str(Path.cwd()),
        )
        log_event("restart_attempt", pid=proc.pid)
        return True
    except Exception as e:
        log_event("restart_failed", error=str(e))
        return False


def escalate_needs_human(diags: dict):
    """Write NEEDS-HUMAN to blockers file."""
    BLOCKERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = f"""
## NEEDS-HUMAN: Portal auto-restart failed (auto_restart.py)
- **Time:** {diags['timestamp']}
- **Port:** {PORTAL_PORT} not responding after {MAX_ATTEMPTS} restart attempts
- **PID found:** {diags.get('portal_pid', 'none')}
- **Diagnostics:** {json.dumps(diags, default=str)}
- **Unblock step:** Manually run `python agent_portal.py` and verify port {PORTAL_PORT} responds.
"""
    with open(BLOCKERS_FILE, "a") as f:
        f.write(entry)
    log_event("escalated", detail="NEEDS-HUMAN written to memory/ops/blockers.md")


def run_check(simulate_down: bool = False) -> dict:
    """Main check-and-restart logic. Returns status dict."""
    result = {"ts": ts(), "portal_up": False, "restarts_attempted": 0, "recovered": False}

    # Step 1: Check if portal is up
    if simulate_down:
        log_event("check", portal_up=False, simulated=True)
    else:
        up = is_portal_up()
        result["portal_up"] = up
        log_event("check", portal_up=up)
        if up:
            result["recovered"] = True  # already healthy
            return result

    # Step 2: Attempt restarts
    for attempt in range(1, MAX_ATTEMPTS + 1):
        result["restarts_attempted"] = attempt
        log_event("attempt_start", attempt=attempt)

        if not attempt_restart():
            continue

        time.sleep(RESTART_WAIT_S)

        # Re-check after wait
        recovered = is_portal_up() if not simulate_down else False
        result["portal_up"] = recovered
        log_event("attempt_result", attempt=attempt, recovered=recovered)

        if recovered:
            result["recovered"] = True
            elapsed = RESTART_WAIT_S * attempt
            log_event("success", attempts=attempt, elapsed_s=elapsed)
            return result

    # Step 3: All attempts failed - escalate
    diags = get_diagnostics()
    escalate_needs_human(diags)
    result["recovered"] = False
    result["escalated"] = True
    return result


def main():
    simulate = "--test" in sys.argv
    if simulate:
        print("TEST MODE: simulating portal down")
    
    result = run_check(simulate_down=simulate)
    print(f"\n=== RESULT ===")
    print(json.dumps(result, indent=2))
    return 0 if result["recovered"] else 1


if __name__ == "__main__":
    sys.exit(main())
