"""Fleet Incident Auto-Triage (goal #6).

Watches for fleet-incident signals and auto-creates structured incident records:
  memory/ops/incidents/YYYY-MM-DD-<agent>-<event_type>.md

Signals scanned:
  - watchdog.log DOWN events (portal down)
  - agents.json + /api/fleet/status if reachable (agent wedged/not-loaded/host-down)

Each record includes: timestamp, classification, action taken, resolution status.
Auto-assigns recovery to Mechanic when the corrective action was a WinRM reboot.

Usage:
  python memory/orchestrator/incident_triage.py              # scan + triage
  python memory/orchestrator/incident_triage.py --resolve <stem>  # mark resolved
"""
import json, re, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
INCIDENTS_DIR = BASE / "memory" / "ops" / "incidents"
WATCHDOG_LOG = BASE / "memory" / "ops" / "watchdog.log"
STATE_FILE = Path(__file__).resolve().parent / ".incident_triage_state.json"

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def today_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen_hashes": []}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def line_hash(line):
    return hashlib.md5(line.strip().encode()).hexdigest()[:12]

def parse_event_date(line):
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', line)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', line)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{y}-{mo:02d}-{d:02d}"
    return today_str()

def classify(event_type, agent=None):
    if "winrm" in event_type or "reboot" in event_type:
        return {"category": "infrastructure", "severity": "high", "action": "WinRM reboot"}
    if "wedged" in event_type or "stall" in event_type:
        return {"category": "agent", "severity": "medium", "action": "Restart agent backend"}
    if "not_loaded" in event_type:
        return {"category": "agent", "severity": "medium", "action": "Load model via Studio API"}
    if "host_down" in event_type or "unreachable" in event_type:
        return {"category": "infrastructure", "severity": "high", "action": "WinRM reboot + verify services"}
    if "portal" in event_type:
        return {"category": "infrastructure", "severity": "high", "action": "PortalRun restart"}
    return {"category": "unknown", "severity": "low", "action": "Investigate manually"}

def assign_recovery(action, category=None):
    # Goal #6 rule: WinRM reboot -> Mechanic (ops recovery).
    if "WinRM" in action or "reboot" in action:
        return "Mechanic"
    # Agent-backend issues (wedge / model load) are orchestration decisions.
    if category == "agent":
        return "Orchestrator"
    # Infrastructure (portal, host-down) defaults to ops.
    return "Mechanic"

def write_incident(event_type, agent=None, detail="", source="auto", date_key=None):
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    cls = classify(event_type, agent)
    assignee = assign_recovery(cls["action"], cls["category"])
    ts = now_iso()
    dk = date_key or today_str()
    target = agent or "fleet"
    fname = f"{dk}-{target}-{event_type}.md"
    fpath = INCIDENTS_DIR / fname
    if fpath.exists():
        existing = fpath.read_text()
        with open(fpath, "a") as f:
            f.write(f"\n## Re-detected {ts}\n- Source: {source}\n- Detail: {detail or 'repeated signal'}\n")
        return fpath
    content = f"""# Incident: {event_type.replace('_', ' ').title()} - {agent or 'Fleet-wide'}

- **ID:** {fname}
- **Detected:** {ts}
- **Source:** {source}
- **Classification:** {cls['category']}
- **Severity:** {cls['severity']}
- **Action Taken:** {cls['action']}
- **Assigned To:** {assignee}
- **Status:** OPEN

## Detail
{detail or 'Auto-detected by incident_triage.py'}

## Resolution
- [ ] Acknowledged
- [ ] Action executed
- [ ] Verified recovery
"""
    fpath.write_text(content)
    return fpath

def resolve_incident(stem):
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    matches = list(INCIDENTS_DIR.glob(f"*{stem}*.md"))
    if not matches:
        print(f"ERROR: no incident matching '{stem}'")
        return None
    fpath = matches[0]
    text = fpath.read_text()
    text = text.replace("- **Status:** OPEN", f"- **Status:** RESOLVED ({now_iso()})")
    text = text.replace("- [ ] ", "- [x] ")
    fpath.write_text(text)
    return fpath

def scan_watchdog(state):
    incidents = []
    if not WATCHDOG_LOG.exists():
        return incidents
    lines = WATCHDOG_LOG.read_text().strip().split("\n")
    for line in lines:
        if "DOWN detected" not in line:
            continue
        h = line_hash(line)
        if h in state["seen_hashes"]:
            continue
        state["seen_hashes"].append(h)
        date_key = parse_event_date(line)
        incidents.append({"event_type": "portal_down", "agent": "fleet", "detail": f"watchdog.log: {line.strip()}", "source": "watchdog.log scan", "date_key": date_key})
    return incidents

def scan_agent_status(state):
    """Check agents.json for not-loaded agents (best-effort, no network needed)."""
    incidents = []
    agents_file = BASE / "agents.json"
    if not agents_file.exists():
        return incidents
    try:
        data = json.loads(agents_file.read_text())
        agents = data.get("agents", []) if isinstance(data, dict) else data
    except Exception:
        return incidents
    for a in agents:
        name = a.get("name", "?")
        model_id = a.get("model_id", "")
        h = line_hash(f"agent_status:{name}:{model_id}")
        if h in state["seen_hashes"]:
            continue
        # Only flag agents with empty/missing model binding as potential not-loaded
        if not model_id:
            state["seen_hashes"].append(h)
            incidents.append({"event_type": "not_loaded", "agent": name, "detail": f"Agent {name} has no model_id binding in agents.json", "source": "agents.json scan"})
    return incidents

def triage(incidents):
    created = []
    for inc in incidents:
        fpath = write_incident(inc["event_type"], inc.get("agent"), inc.get("detail", ""), inc.get("source", "auto"), inc.get("date_key"))
        cls = classify(inc["event_type"])
        assignee = assign_recovery(cls["action"], cls["category"])
        print(f"  [{cls['severity'].upper()}] {fpath.relative_to(BASE)} -> assigned: {assignee}")
        created.append(fpath)
    return created

def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--resolve":
        fpath = resolve_incident(sys.argv[2])
        if fpath:
            print(f"RESOLVED: {fpath.relative_to(BASE)}")
        return
    if len(sys.argv) >= 3 and sys.argv[1] == "--simulate":
        # Acceptance-test path: inject a synthetic incident (e.g. wedge, winrm_reboot).
        event_type = sys.argv[2]
        agent = sys.argv[3] if len(sys.argv) >= 4 else "researcher"
        fpath = write_incident(event_type, agent, detail=f"SIMULATED {event_type} for acceptance test", source="--simulate")
        cls = classify(event_type)
        print(f"SIMULATED: {fpath.relative_to(BASE)} | severity={cls['severity']} | assignee={assign_recovery(cls['action'], cls['category'])}")
        return
    state = load_state()
    all_incidents = []
    all_incidents.extend(scan_watchdog(state))
    all_incidents.extend(scan_agent_status(state))
    save_state(state)
    if not all_incidents:
        print("No new incidents detected.")
        return
    print(f"Detected {len(all_incidents)} new incident(s):")
    triage(all_incidents)

if __name__ == "__main__":
    main()
