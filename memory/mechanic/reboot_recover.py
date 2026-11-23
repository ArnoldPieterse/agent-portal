#!/usr/bin/env python3
"""
reboot_recover.py - Boot-detect recovery sequence.
Deployed to all 4 hosts; invoked by schtask "RebootRecover" on system start.

Logic:
  1. Check Windows Event Log (System, ID 6008) for unexpected shutdown since last boot.
  2. If unexpected shutdown found: restart portal, verify health, log result.
  3. If clean shutdown or no prior event: log NO-OP and exit 0.

Idempotent: safe to run multiple times; only acts if portal is actually down.
Usage:
  python reboot_recover.py            # auto-detect + recover
  python reboot_recover.py --force    # skip detection, force recovery
  python reboot_recover.py --dry-run  # detect only, no action
"""
import json, os, sys, time, socket, subprocess, datetime, pathlib, platform

PORTAL_PORT = 8099
PORTAL_SCRIPT = "agent_portal.py"
RECOVERY_TIMEOUT_S = 300
OUT = pathlib.Path(__file__).parent / "reboot-recovery.jsonl"
HOST_NAME = platform.node()


def log_entry(entry):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "a") as f:
        f.write(json.dumps(entry) + "\n")


def detect_unexpected_shutdown():
    """
    Check Windows Event Log System channel for Event ID 6008 (unexpected shutdown).
    Returns True if an unexpected shutdown was found since last boot.
    On non-Windows or if event log unavailable, returns False (assume clean).
    """
    if platform.system() != "Windows":
        return False
    try:
        r = subprocess.run(
            'powershell -NoProfile -Command '
            '"Get-WinEvent -LogName System -MaxEvents 50 | Where-Object { $_.Id -eq 6008 } | Select-Object -First 1 TimeCreated, Id"',
            shell=True, capture_output=True, text=True, timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        if r.returncode == 0 and "6008" in r.stdout:
            return True
    except (subprocess.TimeoutExpired, Exception):
        pass
    return False


def is_portal_running():
    """Check if portal is listening on PORTAL_PORT."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        r = s.connect_ex(("127.0.0.1", PORTAL_PORT))
        s.close()
        return r == 0
    except (socket.timeout, OSError):
        return False


def start_portal():
    """
    Start the portal process in background.
    Returns (success: bool, pid or error string).
    """
    script_dir = pathlib.Path(__file__).parent.parent.parent  # project root
    portal_path = script_dir / PORTAL_SCRIPT
    if not portal_path.exists():
        return False, f"{PORTAL_SCRIPT} not found at {portal_path}"
    try:
        p = subprocess.Popen(
            [sys.executable, str(portal_path)],
            cwd=str(script_dir),
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        return True, p.pid
    except Exception as e:
        return False, str(e)


def wait_healthy(timeout_s=RECOVERY_TIMEOUT_S):
    """Poll portal until healthy. Returns (ok, elapsed_s)."""
    t0 = time.monotonic()
    while (time.monotonic() - t0) < timeout_s:
        if is_portal_running():
            return True, (time.monotonic() - t0)
        time.sleep(5)
    return False, (time.monotonic() - t0)


def main():
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv

    print(f"[reboot_recover] {ts} host={HOST_NAME}")

    # Step 1: Detect unexpected shutdown (skip if --force)
    if not force:
        unexpected = detect_unexpected_shutdown()
        if not unexpected:
            entry = {"ts": ts, "host": HOST_NAME, "type": "boot_detect",
                     "unexpected_shutdown": False, "action": "NO-OP",
                     "verdict": "CLEAN BOOT - no recovery needed"}
            log_entry(entry)
            print("  Clean boot detected. No recovery needed.")
            return
        print("  Unexpected shutdown detected.")

    # Step 2: Check if portal is already running (idempotency)
    if is_portal_running():
        entry = {"ts": ts, "host": HOST_NAME, "type": "boot_recover",
                 "unexpected_shutdown": True, "portal_status": "ALREADY_RUNNING",
                 "action": "NO-OP", "verdict": "PASS - portal already up"}
        log_entry(entry)
        print("  Portal already running. No action needed.")
        return

    if dry_run:
        entry = {"ts": ts, "host": HOST_NAME, "type": "boot_recover_dryrun",
                 "unexpected_shutdown": True, "portal_status": "DOWN",
                 "action": "WOULD_START", "verdict": "DRY-RUN - portal down, would start"}
        log_entry(entry)
        print("  [DRY-RUN] Portal is down. Would start it.")
        return

    # Step 3: Start portal
    print("  Starting portal...")
    ok, pid_or_err = start_portal()
    if not ok:
        entry = {"ts": ts, "host": HOST_NAME, "type": "boot_recover",
                 "unexpected_shutdown": True, "action": "START_FAILED",
                 "error": str(pid_or_err), "verdict": "FAIL"}
        log_entry(entry)
        print(f"  FAIL: {pid_or_err}")
        sys.exit(1)

    print(f"  Portal started (PID {pid_or_err}). Waiting for health...")

    # Step 4: Wait for healthy
    healthy, elapsed = wait_healthy()
    entry = {
        "ts": ts, "host": HOST_NAME, "type": "boot_recover",
        "unexpected_shutdown": True, "action": "STARTED",
        "pid": pid_or_err, "recovered": healthy,
        "recovery_s": round(elapsed, 1),
        "verdict": f"{'PASS' if healthy else 'FAIL'} - recovered in {elapsed:.1f}s"
    }
    log_entry(entry)
    print(f"  Verdict: {entry['verdict']}")
    sys.exit(0 if healthy else 1)


if __name__ == "__main__":
    main()
