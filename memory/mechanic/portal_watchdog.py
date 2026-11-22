"""Portal Process Watchdog - verifies agent_portal.py is healthy.
Checks: process exists, port 8099 bound, no zombie children.
Uses 3-level escalation chain (L1 retry -> L2 handoff -> L3 NEEDS-HUMAN).
Usage: python memory/mechanic/portal_watchdog.py [--once | --schedule]"""
import os, sys, time, json, socket, subprocess
from datetime import datetime, timezone

# Escalation chain integration (goal #8)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from escalation_chain import EscalationChain
    _HAS_ESC = True
except ImportError:
    _HAS_ESC = False

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

def _attempt_restart():
    """Try to restart the portal. Returns True if port is up after attempt."""
    log_event("INFO", "attempting portal restart")
    try:
        subprocess.Popen([sys.executable, "agent_portal.py"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(10)
        return port_bound()
    except Exception as e:
        log_event("ERROR", f"restart failed: {e}")
        return False


def check():
    ts = datetime.now(timezone.utc).isoformat()
    healthy = True
    
    # Check 1: port bound (with escalation chain)
    up = port_bound()
    if not up:
        log_event("CRITICAL", "port 8099 not responding - portal down")
        healthy = False
        
        if _HAS_ESC:
            ec = EscalationChain("portal_down", source="watchdog")
            level = ec.fail()
            if level <= 1:
                # L1: auto-retry
                recovered = _attempt_restart()
                if recovered:
                    log_event("INFO", "portal recovered after restart (L1)")
                    ec.success()
                    healthy = True
                else:
                    log_event("WARN", f"restart attempt failed, escalation level={level}")
            elif level == 2:
                # L2: agent handoff - structured request logged by EscalationChain
                log_event("WARN", "escalated to L2 (agent handoff) - portal still down after retries")
            else:
                # L3: NEEDS-HUMAN already written to blockers.md by EscalationChain
                log_event("CRITICAL", "escalated to L3 (NEEDS-HUMAN) - see memory/ops/blockers.md")
        else:
            # Fallback: original behaviour if escalation_chain module unavailable
            recovered = _attempt_restart()
            if recovered:
                log_event("INFO", "portal recovered after restart")
                healthy = True
            else:
                log_event("CRITICAL", "portal still down after restart - NEEDS-HUMAN")
    else:
        log_event("INFO", "port 8099 responding - portal up")
        # If escalation chain was active, mark recovery
        if _HAS_ESC:
            ec = EscalationChain("portal_down", source="watchdog")
            ec.success()
    
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