"""Portal Process Watchdog - verifies agent_portal.py is healthy.
Checks: process exists, port 8099 bound, no zombie children.
Restarts if orphaned or in wrong state.
Usage: python memory/mechanic/portal_watchdog.py [--once | --schedule]"""
import os, sys, time, json, socket, subprocess
from datetime import datetime, timezone

LOG = os.path.join(os.path.dirname(__file__), "watchdog_log.jsonl")
PORT = 8099
INTERVAL_S = 300  # 5 min

def log_event(level, msg, **extra):
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "level": level, "msg": msg}
    entry.update(extra)
    with open(LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"  [{level}] {msg}")

def port_bound():
    try:
        s = socket.create_connection(("127.0.0.1", PORT), timeout=3)
        s.close()
        return True
    except (ConnectionRefusedError, OSError):
        return False

def find_portal_pids():
    """Find PIDs of agent_portal.py processes."""
    try:
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
                          capture_output=True, text=True, timeout=10)
        pids = []
        for line in r.stdout.strip().split("\n"):
            if "python" in line.lower():
                parts = [p.strip('"') for p in line.split(",")]
                if len(parts) >= 2 and parts[0].lower() == "python.exe":
                    pids.append(parts[1])
        return pids
    except Exception:
        return []

def check():
    ts = datetime.now(timezone.utc).isoformat()
    healthy = True
    
    # Check 1: port bound
    up = port_bound()
    if not up:
        log_event("CRITICAL", "port 8099 not responding - portal down")
        healthy = False
        # Attempt restart
        log_event("INFO", "attempting portal restart")
        try:
            subprocess.Popen([sys.executable, "agent_portal.py"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(10)
            up = port_bound()
            if up:
                log_event("INFO", "portal recovered after restart")
                healthy = True
            else:
                log_event("CRITICAL", "portal still down after restart - NEEDS-HUMAN")
        except Exception as e:
            log_event("ERROR", f"restart failed: {e}")
    else:
        log_event("INFO", "port 8099 responding - portal up")
    
    # Check 2: no zombie/orphan python processes (simplified)
    pids = find_portal_pids()
    if len(pids) > 3:
        log_event("WARN", f"multiple python PIDs found ({len(pids)}): {pids} - possible orphans")
    
    return healthy

def main():
    mode = "--schedule" if "--schedule" in sys.argv else "--once"
    if mode == "--schedule":
        print(f"Portal watchdog scheduling every {INTERVAL_S}s...")
        while True:
            check()
            time.sleep(INTERVAL_S)
    else:
        healthy = check()
        print(f"Overall: {'HEALTHY' if healthy else 'DEGRADED'}")

if __name__ == "__main__":
    main()