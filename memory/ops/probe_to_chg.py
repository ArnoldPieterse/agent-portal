"""Probe-to-CHG bridge: auto-create evolution entities on CRIT probe events.

Goal #5 (Mechanic): host down or critical port dead -> CHG entity (status=candidate)
so outages are trackable alongside other project changes in the evolution layer.

Usage: python memory/ops/probe_to_chg.py [--dry-run]
  Reads last N entries from memory/ops/probe-evidence.jsonl; for each CRIT event
  not yet bridged, proposes a CHG entity via evolution.py.
  
  --dry-run: print what would be proposed without writing to population.json.

Idempotency: tracks bridged events in memory/ops/probe-to-chg-state.json
(event_id -> chg_id mapping). Re-running never double-creates.
"""
import json, os, sys, subprocess, datetime

OPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE = os.path.join(OPS_DIR, "probe-evidence.jsonl")
STATE_FILE = os.path.join(OPS_DIR, "probe-to-chg-state.json")
EVOLUTION_PY = os.path.join(os.path.dirname(os.path.dirname(OPS_DIR)), "evolution.py")

# Critical status values that trigger CHG creation
CRIT_STATUSES = {"TIMEOUT", "ERROR:13", "REFUSED", "DOWN"}
# Ports considered critical (host is effectively down if these are dead)
CRITICAL_PORTS = {8099, 445}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"bridged": {}}

def save_state(state):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)

def read_crit_events():
    """Read probe-evidence.jsonl and return CRIT host-level events not yet bridged.
    
    Data format: each line is a full probe run with 'results' array of per-host/port entries.
    We extract host-level outages: a host is CRIT if ALL its critical ports are down.
    One CHG entity per unique (host, date) pair - first detection time is recorded.
    """
    if not os.path.exists(EVIDENCE):
        return []
    state = load_state()
    # Collect first-seen outage per (host, date)
    seen = {}  # eid -> ev
    with open(EVIDENCE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            run = json.loads(line)
            ts = run.get("ts", "?")
            results = run.get("results", [])
            
            # Group by host, check if ALL critical ports are down
            host_ports = {}
            for r in results:
                host = r.get("host", "?")
                port = r.get("port", 0)
                status = r.get("status", "")
                sev = r.get("severity", "")
                if host not in host_ports:
                    host_ports[host] = []
                host_ports[host].append({"port": port, "status": status, "severity": sev})
            
            for host, ports in host_ports.items():
                crit_port_entries = [p for p in ports if p["port"] in CRITICAL_PORTS]
                if not crit_port_entries:
                    continue
                all_dead = all(p["severity"] == "CRIT" or p["status"] in CRIT_STATUSES for p in crit_port_entries)
                if not all_dead:
                    continue
                date_key = ts[:10]  # YYYY-MM-DD
                eid = f"{date_key}_{host}_outage"
                # Only keep first detection per (host, date)
                if eid not in seen:
                    seen[eid] = {"ts": ts, "host": host, "type": "host_down", "ports": ports}
    
    # Filter out already-bridged
    crits = [(eid, ev) for eid, ev in seen.items() if eid not in state["bridged"]]
    return crits

def propose_chg(event_id, event, dry_run=False):
    """Propose a CHG entity for this outage event."""
    host = event.get("host", "unknown")
    etype = event.get("type", "unknown")
    ts = event.get("ts", datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
    
    spec = f"Outage: {etype} on {host} at {ts}"
    target = f"memory/ops/probe-evidence.jsonl#{event_id}"
    params = {"host": host, "type": etype, "detected_at": ts, "source": "probe-to-chg"}
    tests = [{"name": "recovery_probe", "cmd": f"python memory/ops/fleet_probe_v2.py --once --host {host}"}]
    
    cmd = [sys.executable, EVOLUTION_PY, "propose",
           "--kind", "code_block",
           "--spec", spec,
           "--target", target,
           "--params", json.dumps(params),
           "--tests", json.dumps(tests),
           "--note", f"Auto-created by probe-to-chg bridge (event {event_id})"]
    
    if dry_run:
        print(f"[DRY-RUN] Would propose: {spec}")
        print(f"  target={target}")
        print(f"  params={json.dumps(params)}")
        return None
    
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    out = r.stdout.strip()
    err = r.stderr.strip()
    if r.returncode != 0:
        print(f"ERROR proposing CHG for {event_id}: {err}")
        return None
    
    # Extract CHG ID from output like "PROPOSED CHG-0003 (code_block gen 1, candidate)"
    chg_id = out.split()[1] if len(out.split()) > 1 else "UNKNOWN"
    print(f"Bridged event {event_id} -> {chg_id}")
    return chg_id

def main():
    dry_run = "--dry-run" in sys.argv
    crits = read_crit_events()
    
    if not crits:
        print("No unbridged CRIT events found.")
        return
    
    state = load_state()
    for eid, ev in crits:
        chg_id = propose_chg(eid, ev, dry_run=dry_run)
        if chg_id and not dry_run:
            state["bridged"][eid] = {"chg_id": chg_id, "bridged_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
    
    if not dry_run:
        save_state(state)
    
    print(f"Done. {len(crits)} CRIT event(s) processed ({'dry-run' if dry_run else 'applied'}).")

if __name__ == "__main__":
    main()
