#!/usr/bin/env python3
"""
reboot_recovery_test.py - Simulated kill+restart test for portal recovery.

Usage:
  python reboot_recovery_test.py --dry-run   # check all 4 hosts, no kill
  python reboot_recovery_test.py             # live: kill portal PID, wait for recovery

Logs to memory/mechanic/reboot-recovery.jsonl (one JSON line per run).
Acceptance: portal recovers within 5 min of kill; all 4 hosts reachable post-recovery.
"""
import json, os, sys, time, socket, subprocess, datetime, pathlib

PORTAL_HOST = "127.0.0.1"
PORTAL_PORT = 8099
RECOVERY_TIMEOUT_S = 300  # 5 min
OUT = pathlib.Path(__file__).parent / "reboot-recovery.jsonl"

# Hosts to check (name, ip, port)
HOSTS = [
    ("White", "127.0.0.1", 8099),
    ("Pale", "IP_PALE", 8888),
    ("Black", "IP_BLACK", 8888),
    ("Red", "IP_RED", 8888),
]


def tcp_check(ip, port, timeout=3):
    """Return (ok: bool, latency_ms: float)."""
    t0 = time.monotonic()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        r = s.connect_ex((ip, port))
        ms = (time.monotonic() - t0) * 1000
        s.close()
        return (r == 0, ms)
    except (socket.timeout, OSError):
        return (False, (time.monotonic() - t0) * 1000)


def find_portal_pid():
    """Find the PID of agent_portal.py via netstat + tasklist."""
    try:
        r = subprocess.run(
            f'netstat -ano | findstr ":{PORTAL_PORT}" | findstr LISTENING',
            shell=True, capture_output=True, text=True
        )
        lines = r.stdout.strip().split("\n")
        for line in lines:
            parts = line.split()
            if len(parts) >= 5 and parts[3].startswith("0.0.0.0") or (len(parts) >= 5 and ":8099" in parts[1]):
                return int(parts[-1])
    except Exception:
        pass
    return None


def kill_portal(pid):
    """Kill the portal process."""
    r = subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True, text=True)
    return r.returncode == 0


def wait_for_recovery(timeout_s=RECOVERY_TIMEOUT_S):
    """Poll portal port until it accepts connections. Returns (recovered: bool, elapsed_s)."""
    t0 = time.monotonic()
    while (time.monotonic() - t0) < timeout_s:
        ok, _ = tcp_check(PORTAL_HOST, PORTAL_PORT, timeout=2)
        if ok:
            return True, (time.monotonic() - t0)
        time.sleep(5)
    return False, (time.monotonic() - t0)


def check_hosts():
    """Check all 4 hosts. Returns dict of results."""
    results = {}
    for name, ip, port in HOSTS:
        ok, ms = tcp_check(ip, port, timeout=5)
        results[name] = {"tcp": f"{ip}:{port}", "status": "PASS" if ok else "FAIL", "latency_ms": round(ms, 1)}
    return results


def log_entry(entry):
    """Append a JSON line to the recovery log."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    dry = "--dry-run" in sys.argv
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if dry:
        print(f"[DRY-RUN] Reboot recovery check at {ts}")
        results = check_hosts()
        passed = sum(1 for v in results.values() if v["status"] == "PASS")
        entry = {"ts": ts, "type": "reboot_dryrun", "results": results,
                 "verdict": f"{passed}/{len(HOSTS)} PASS"}
        log_entry(entry)
        for name, r in results.items():
            print(f"  {name}: {r['status']} ({r['latency_ms']}ms)")
        print(f"\nVerdict: {entry['verdict']}")
        return

    # Live mode: kill + wait for recovery
    print(f"[LIVE] Reboot recovery test at {ts}")
    pid = find_portal_pid()
    if not pid:
        entry = {"ts": ts, "type": "reboot_live", "error": "portal PID not found (not running?)",
                 "results": check_hosts(), "verdict": "SKIP - portal not running"}
        log_entry(entry)
        print(f"  SKIP: portal not running on :{PORTAL_PORT}")
        return

    print(f"  Portal PID: {pid}")
    print(f"  Killing...")
    killed = kill_portal(pid)
    if not killed:
        entry = {"ts": ts, "type": "reboot_live", "error": f"kill failed for PID {pid}"}
        log_entry(entry)
        print(f"  FAIL: could not kill PID {pid}")
        return

    print(f"  Waiting up to {RECOVERY_TIMEOUT_S}s for recovery...")
    recovered, elapsed = wait_for_recovery()
    results = check_hosts() if recovered else {"White": {"status": "FAIL (not recovered)"}}
    passed = sum(1 for v in results.values() if isinstance(v, dict) and v.get("status") == "PASS")

    entry = {
        "ts": ts, "type": "reboot_live", "pid_killed": pid,
        "recovered": recovered, "recovery_s": round(elapsed, 1),
        "results": results, "verdict": f"{'PASS' if recovered and elapsed < RECOVERY_TIMEOUT_S else 'FAIL'}"
    }
    log_entry(entry)
    print(f"\n  Recovered: {recovered} in {elapsed:.1f}s")
    print(f"  Hosts post-recovery: {passed}/{len(HOSTS)} PASS")
    print(f"  Verdict: {entry['verdict']}")


if __name__ == "__main__":
    main()
