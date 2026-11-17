#!/usr/bin/env python3
"""restart_portal.py - Clean portal restart: read PID, kill, re-run task, verify.
Goal #9 item 2: replaces manual taskkill+re-run pattern with a single verified script.

Usage: python restart_portal.py [--dry-run]
Exit: 0 = success (new PID confirmed), 1 = failure

Runbook note: Always use --dry-run first to confirm the target PID before killing.
"""
import json, os, signal, socket, subprocess, sys, time
from datetime import datetime, timezone

PID_FILE = "_portal_pid.txt"
TASK_NAME = "PortalRun"
PORT = 8099
VERIFY_TIMEOUT = 15  # seconds to wait for portal to come back

def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts} {msg}"
    print(line)
    # Append to ops log
    try:
        with open("memory/ops/restart-portal.jsonl", "a") as f:
            f.write(json.dumps({"ts": ts, "msg": msg}) + "\n")
    except OSError:
        pass

def get_pid():
    """Read portal PID from _portal_pid.txt or find via port."""
    if os.path.exists(PID_FILE):
        try:
            pid = int(open(PID_FILE).read().strip())
            return pid, f"from {PID_FILE}"
        except (ValueError, OSError) as e:
            log(f"WARN: could not parse {PID_FILE}: {e}")
    # Fallback: find PID listening on port 8099 via netstat
    try:
        out = subprocess.check_output(["netstat", "-ano"], text=True, timeout=10)
        for line in out.splitlines():
            if f":{PORT} " in line and "LISTENING" in line:
                pid = int(line.strip().split()[-1])
                return pid, "from netstat"
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        log(f"WARN: netstat lookup failed: {e}")
    return None, "not found"

def is_port_open(port=PORT, timeout=3.0):
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
        sock.close()
        return True
    except (PermissionError, OSError):
        return False

def kill_pid(pid):
    """Kill the portal process."""
    log(f"KILL: sending termination to PID {pid}")
    try:
        # On Windows, taskkill is more reliable than signal.SIGTERM
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                      capture_output=True, timeout=10)
        time.sleep(2)  # Give it time to die
        return True
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f"ERROR: taskkill failed: {e}")
        return False

def rerun_task():
    """Re-run the PortalRun scheduled task."""
    log(f"RUN: schtasks /run /tn {TASK_NAME}")
    try:
        result = subprocess.run(["schtasks", "/run", "/tn", TASK_NAME],
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return True
        log(f"WARN: schtasks rc={result.returncode}: {result.stderr.strip()}")
        # Fallback: try direct python launch
        log("FALLBACK: launching portal directly")
        subprocess.Popen([sys.executable, "agent_portal.py"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (OSError, subprocess.TimeoutExpired) as e:
        log(f"ERROR: task re-run failed: {e}")
        return False

def verify_new_pid(old_pid):
    """Wait for portal to come back with a DIFFERENT PID."""
    log(f"VERIFY: waiting up to {VERIFY_TIMEOUT}s for new portal on :{PORT}...")
    deadline = time.time() + VERIFY_TIMEOUT
    while time.time() < deadline:
        if is_port_open():
            new_pid, source = get_pid()
            if new_pid and new_pid != old_pid:
                log(f"OK: new PID {new_pid} confirmed (old was {old_pid})")
                return True, new_pid
            elif new_pid == old_pid:
                # Same PID - process didn't actually die
                log(f"WARN: same PID {new_pid} still listening; kill may have failed")
                return False, new_pid
        time.sleep(1)
    log("FAIL: portal did not come back within timeout")
    return False, None

def main():
    dry_run = "--dry-run" in sys.argv
    
    pid, source = get_pid()
    if pid is None:
        log("FAIL: no portal PID found; nothing to restart")
        sys.exit(1)
    
    log(f"TARGET: PID {pid} ({source})")
    
    if dry_run:
        port_open = is_port_open()
        log(f"DRY-RUN: portal port {PORT} {'open' if port_open else 'closed'}; "
            f"would kill PID {pid} and re-run {TASK_NAME}")
        sys.exit(0)
    
    # Execute restart sequence
    if not kill_pid(pid):
        log("FAIL: could not kill old process")
        sys.exit(1)
    
    if not rerun_task():
        log("FAIL: could not re-run portal task")
        sys.exit(1)
    
    success, new_pid = verify_new_pid(pid)
    if success:
        log(f"SUCCESS: portal restarted. Old PID {pid} -> New PID {new_pid}")
        sys.exit(0)
    else:
        log("FAIL: restart did not complete successfully")
        sys.exit(1)

if __name__ == "__main__":
    main()
