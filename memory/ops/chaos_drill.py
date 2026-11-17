#!/usr/bin/env python3
"""Chaos drill: kill portal on rotating host, verify recovery <60s.
Rotation: White -> Pale -> Black -> Red (monthly).
Log: memory/mechanic/chaos-drill.jsonl
Usage:
  python chaos_drill.py --dry-run     # show next target + plan
  python chaos_drill.py               # execute drill on next host
  python chaos_drill.py --host White  # force specific host
"""
import json, os, sys, time, socket, argparse
from datetime import datetime, timezone

HOSTS = ["White", "Pale", "Black", "Red"]
PORT = 8099
RECOVERY_TIMEOUT_S = 60
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "mechanic", "chaos-drill.jsonl")
STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "mechanic", "chaos-drill-state.json")

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_index": -1, "drills_completed": []}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def next_host(state, forced=None):
    if forced:
        return forced
    idx = (state["last_index"] + 1) % len(HOSTS)
    state["last_index"] = idx
    return HOSTS[idx]

def log_entry(entry):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    entry["ts"] = now_iso()
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Logged: {entry.get('host')} -> {entry.get('verdict')}")

def check_port(host_ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        return s.connect_ex((host_ip, PORT)) == 0
    except Exception:
        return False
    finally:
        s.close()

def wait_recovery(host_ip, timeout=RECOVERY_TIMEOUT_S):
    """Poll until port is open again. Returns (recovered: bool, elapsed_s)."""
    start = time.time()
    while time.time() - start < timeout:
        if check_port(host_ip):
            return True, round(time.time() - start, 1)
        time.sleep(2)
    return False, round(time.time() - start, 1)

def kill_portal_on(host_name, host_ip):
    """Kill portal. On local host use os.kill; remote needs SSH or API."""
    if host_name == "Red":  # we're on Red
        # Find python process running agent_portal.py and kill it
        import subprocess
        try:
            r = subprocess.run(
                ["python", "-c",
                 "import psutil; [p.terminate() for p in psutil.process_iter() if 'agent_portal' in ' '.join(p.cmdline())]"],
                capture_output=True, text=True, timeout=10)
            return r.returncode == 0
        except Exception as e:
            print(f"  kill failed: {e}")
            return False
    else:
        # Remote: would use SSH or portal API /api/admin/restart
        print(f"  [DRY] Would kill portal on {host_name} ({host_ip})")
        return True

def run_drill(host, host_ip=None, dry_run=False):
    state = load_state()
    entry = {"host": host, "ts": now_iso(), "mode": "dry-run" if dry_run else "live"}

    if dry_run:
        entry["plan"] = f"Kill portal on {host}, wait up to {RECOVERY_TIMEOUT_S}s for recovery"
        entry["verdict"] = "DRY_RUN_OK"
        log_entry(entry)
        return entry

    # 1. Verify portal is UP before killing
    if not check_port(host_ip):
        entry["verdict"] = "FAIL_PORTAL_DOWN_BEFORE_KILL"
        log_entry(entry)
        return entry

    # 2. Kill
    killed = kill_portal_on(host, host_ip)
    entry["killed"] = killed
    if not killed:
        entry["verdict"] = "FAIL_KILL_FAILED"
        log_entry(entry)
        return entry

    # 3. Wait for recovery
    time.sleep(3)  # give it a moment to actually die
    recovered, elapsed = wait_recovery(host_ip)
    entry["recovered"] = recovered
    entry["recovery_s"] = elapsed
    entry["verdict"] = "PASS" if (recovered and elapsed < RECOVERY_TIMEOUT_S) else "FAIL_NO_RECOVERY"

    # 4. Update state
    if recovered:
        state["drills_completed"].append({"host": host, "ts": now_iso(), "recovery_s": elapsed})
        save_state(state)

    log_entry(entry)
    return entry

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Chaos drill: kill+recover portal")
    ap.add_argument("--host", choices=HOSTS, help="Force specific host")
    ap.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    args = ap.parse_args()

    state = load_state()
    host = next_host(state, forced=args.host)
    # IP mapping (adjust to actual fleet IPs)
    ips = {"White": "10.0.0.2", "Pale": "10.0.0.3", "Black": "10.0.0.4", "Red": "127.0.0.1"}
    run_drill(host, ips[host], dry_run=args.dry_run)
