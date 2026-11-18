#!/usr/bin/env python3
"""boot_recovery.py - Per-host boot-detection + auto-recovery trigger.
Deploy as a Windows scheduled task (ONSTART) on each fleet host.
Waits for Studio :8888 to answer, then invokes the appropriate load routine.
Logs timestamped evidence to memory/ops/boot-recovery-log.jsonl."""

import json, time, datetime, urllib.request, sys, os, platform

STUDIO_PORT = 8888
HOSTNAME = platform.node()
LOG_PATH = os.path.join("memory", "ops", "boot-recovery-log.jsonl")

def log(event, **kw):
    entry = {"ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "host": HOSTNAME, "event": event, **kw}
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(entry, flush=True)

def wait_studio(timeout_min=5):
    """Poll Studio :8888 until it answers /api/health."""
    deadline = time.time() + timeout_min * 60
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{STUDIO_PORT}/api/health", timeout=5) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(5)
    return False

def main():
    log("boot_detected", hostname=HOSTNAME, pid=os.getpid())
    
    # Wait for Studio to come up post-boot
    if not wait_studio(timeout_min=5):
        log("STUDIO_NEVER_UP")
        sys.exit(1)
    log("studio_up")
    
    # Determine which load script to run based on hostname
    host_lower = HOSTNAME.lower()
    if "white" in host_lower:
        cmd = [sys.executable, "fleet_reload.py"]  # white() thread handles local
    elif "black" in host_lower or ".99" in host_lower:
        cmd = [sys.executable, "fleet_reload.py"]  # black() thread
    elif "pale" in host_lower or ".39" in host_lower:
        cmd = [sys.executable, "fleet_reload.py"]  # pale() thread
    elif "red" in host_lower or ".245" in host_lower:
        cmd = [sys.executable, "fleet_reload.py"]  # red() thread
    else:
        log("UNKNOWN_HOST", hostname=HOSTNAME)
        sys.exit(1)
    
    log("invoking_fleet_reload")
    import subprocess
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3000)
    log("fleet_reload_done", returncode=result.returncode, 
        stdout_tail=result.stdout[-500:] if result.stdout else "")
    
    # Verify portal is serving
    try:
        with urllib.request.urlopen("http://127.0.0.1:8099/api/goals", timeout=10) as r:
            log("portal_up", status=r.status)
    except Exception as e:
        log("portal_down_after_recovery", error=str(e)[:200])

if __name__ == "__main__":
    main()
