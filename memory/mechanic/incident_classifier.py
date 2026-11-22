"""Incident Auto-Classification - Mechanic Goal #9 (Cycle 10).

When an incident is detected, auto-classify severity:
  P1 (fleet-down): portal unreachable or >3 agents affected
  P2 (degraded):   1-2 agents down or host at >90% resources
  P3 (minor):      single agent slow or one metric warning
  P4 (info):       threshold crossed but no user impact

Usage:
    python memory/mechanic/incident_classifier.py --selftest
    python memory/mechanic/incident_classifier.py --classify '{"type":"host_down","host":"pale"}'
"""

import json
import os
import sys
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OPS_DIR = os.path.join(BASE_DIR, "..", "ops")
INCIDENTS_FILE = os.path.normpath(os.path.join(OPS_DIR, "incidents.jsonl"))
ALERTS_FILE = os.path.normpath(os.path.join(OPS_DIR, "incident-alerts.jsonl"))

# Severity levels (lower number = more severe)
SEVERITY_P1 = 1
SEVERITY_P2 = 2
SEVERITY_P3 = 3
SEVERITY_P4 = 4

SEVERITY_NAMES = {1: "P1", 2: "P2", 3: "P3", 4: "P4"}


def classify(incident: dict) -> dict:
    """Classify an incident into severity level.
    
    Args:
        incident: dict with at least 'type' key. Optional fields:
            - type: str (portal_down, host_down, agent_down, agent_slow, metric_warning, threshold_crossed)
            - host: str
            - agents_affected: int (number of agents impacted)
            - resource_pct: float (resource utilization 0-100)
            - response_time_ms: float (agent response time)
            - metric: str (which metric triggered)
            - value: float (metric value)
            - threshold: float (threshold that was crossed)
    
    Returns:
        dict with severity, level (P1-P4), rationale, alert_required
    """
    inc_type = incident.get("type", "unknown")
    agents_affected = incident.get("agents_affected", 0)
    resource_pct = incident.get("resource_pct", 0)
    response_time_ms = incident.get("response_time_ms", 0)
    
    # P1: fleet-down - portal unreachable or >3 agents affected
    if inc_type == "portal_down":
        return _result(SEVERITY_P1, f"Portal unreachable - entire fleet down")
    if agents_affected > 3:
        return _result(SEVERITY_P1, f"{agents_affected} agents affected (>3) - fleet-level impact")
    
    # P2: degraded - 1-2 agents down or host at >90% resources
    if inc_type == "host_down":
        return _result(SEVERITY_P2, f"Host '{incident.get('host','unknown')}' down - degraded service")
    if inc_type == "agent_down":
        return _result(SEVERITY_P2, f"{agents_affected} agent(s) down - degraded")
    if resource_pct > 90:
        return _result(SEVERITY_P2, f"Resource at {resource_pct}% (>90%) on '{incident.get('host','unknown')}'")
    
    # P3: minor - single agent slow or one metric warning
    if inc_type == "agent_slow":
        return _result(SEVERITY_P3, f"Agent response time {response_time_ms}ms - slow but functional")
    if inc_type == "metric_warning":
        return _result(SEVERITY_P3, f"Metric '{incident.get('metric','unknown')}' warning: value={incident.get('value')}")
    
    # P4: info - threshold crossed but no user impact
    if inc_type == "threshold_crossed":
        return _result(SEVERITY_P4, f"Threshold crossed ({incident.get('metric','?')}: {incident.get('value')} > {incident.get('threshold')}) - informational")
    
    # Default: P3 for unknown types (err on caution)
    return _result(SEVERITY_P3, f"Unknown incident type '{inc_type}' - defaulting to P3")


def _result(severity: int, rationale: str) -> dict:
    """Build classification result."""
    return {
        "severity": severity,
        "level": SEVERITY_NAMES[severity],
        "rationale": rationale,
        "alert_required": severity <= 2,  # P1 and P2 trigger alerts
        "timestamp": _now(),
    }


def record_incident(incident: dict, classification: dict) -> dict:
    """Write incident + classification to incidents.jsonl."""
    os.makedirs(os.path.dirname(INCIDENTS_FILE), exist_ok=True)
    record = {
        "timestamp": _now(),
        "incident": incident,
        "classification": classification,
    }
    with open(INCIDENTS_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record


def send_alert(classification: dict, incident: dict):
    """Send alert for P1/P2 incidents (append to alerts file)."""
    if not classification.get("alert_required"):
        return None
    os.makedirs(os.path.dirname(ALERTS_FILE), exist_ok=True)
    alert = {
        "timestamp": _now(),
        "level": classification["level"],
        "incident_type": incident.get("type"),
        "host": incident.get("host"),
        "message": f"[{classification['level']}] {classification['rationale']}",
        "action_required": "IMMEDIATE" if classification["severity"] == 1 else "PROMPT",
    }
    with open(ALERTS_FILE, "a") as f:
        f.write(json.dumps(alert) + "\n")
    return alert


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# === SELF-TEST ===

def selftest():
    """Comprehensive self-test battery."""
    print("=== Incident Classifier Self-Test ===")
    results = []
    
    def check(name, cond):
        results.append((name, bool(cond)))
        status = "PASS" if cond else "FAIL"
        print(f"  [{status}] {name}")
    
    # --- P1 scenarios ---
    r = classify({"type": "portal_down"})
    check("P1: portal_down -> severity 1", r["severity"] == 1)
    check("P1: portal_down -> level P1", r["level"] == "P1")
    check("P1: alert required", r["alert_required"] is True)
    
    r = classify({"type": "agent_down", "agents_affected": 5})
    check("P1: >3 agents affected -> severity 1", r["severity"] == 1)
    check("P1: rationale mentions count", "5" in r["rationale"])
    
    # --- P2 scenarios ---
    r = classify({"type": "host_down", "host": "pale"})
    check("P2: host_down -> severity 2", r["severity"] == 2)
    check("P2: level P2", r["level"] == "P2")
    check("P2: alert required", r["alert_required"] is True)
    
    r = classify({"type": "agent_down", "agents_affected": 1})
    check("P2: single agent down -> severity 2", r["severity"] == 2)
    
    r = classify({"type": "metric_warning", "resource_pct": 95, "host": "white"})
    check("P2: resource >90% -> severity 2", r["severity"] == 2)
    
    # --- P3 scenarios ---
    r = classify({"type": "agent_slow", "response_time_ms": 5000})
    check("P3: agent_slow -> severity 3", r["severity"] == 3)
    check("P3: level P3", r["level"] == "P3")
    check("P3: no alert required", r["alert_required"] is False)
    
    r = classify({"type": "metric_warning", "metric": "disk_io", "value": 150})
    check("P3: metric_warning -> severity 3", r["severity"] == 3)
    
    # --- P4 scenarios ---
    r = classify({"type": "threshold_crossed", "metric": "gpu_temp", "value": 86, "threshold": 85})
    check("P4: threshold_crossed -> severity 4", r["severity"] == 4)
    check("P4: level P4", r["level"] == "P4")
    check("P4: no alert required", r["alert_required"] is False)
    
    # --- Boundary conditions ---
    r = classify({"type": "agent_down", "agents_affected": 3})
    check("Boundary: exactly 3 agents -> P2 (not P1)", r["severity"] == 2)
    
    r = classify({"type": "metric_warning", "resource_pct": 90})
    check("Boundary: exactly 90% -> P3 (not P2, needs >90)", r["severity"] == 3)
    
    r = classify({"type": "metric_warning", "resource_pct": 90.1})
    check("Boundary: 90.1% -> P2", r["severity"] == 2)
    
    # --- Unknown type defaults to P3 ---
    r = classify({"type": "something_new"})
    check("Unknown type -> P3 default", r["severity"] == 3)
    
    # --- All results have required fields ---
    for test_inc in [
        {"type": "portal_down"},
        {"type": "host_down", "host": "black"},
        {"type": "agent_slow", "response_time_ms": 3000},
        {"type": "threshold_crossed", "metric": "cpu", "value": 80, "threshold": 75},
    ]:
        r = classify(test_inc)
        check(f"Fields complete for {test_inc['type']}", 
              all(k in r for k in ["severity", "level", "rationale", "alert_required", "timestamp"]))
    
    # --- 5 test scenarios (acceptance criterion) ---
    scenarios = [
        ({"type": "portal_down"}, SEVERITY_P1),
        ({"type": "host_down", "host": "pale"}, SEVERITY_P2),
        ({"type": "agent_slow", "response_time_ms": 8000}, SEVERITY_P3),
        ({"type": "threshold_crossed", "metric": "net_rtt", "value": 210, "threshold": 200}, SEVERITY_P4),
        ({"type": "agent_down", "agents_affected": 4}, SEVERITY_P1),
    ]
    for inc, expected_sev in scenarios:
        r = classify(inc)
        check(f"Scenario: {inc['type']} -> P{expected_sev}", r["severity"] == expected_sev)
    
    # --- Alert firing ---
    p1_class = classify({"type": "portal_down"})
    alert = send_alert(p1_class, {"type": "portal_down"})
    check("P1 triggers alert", alert is not None)
    check("Alert has IMMEDIATE action", alert["action_required"] == "IMMEDIATE")
    
    p3_class = classify({"type": "agent_slow", "response_time_ms": 5000})
    no_alert = send_alert(p3_class, {"type": "agent_slow"})
    check("P3 does NOT trigger alert", no_alert is None)
    
    # --- Incident recording ---
    inc = {"type": "host_down", "host": "white"}
    cls = classify(inc)
    record = record_incident(inc, cls)
    check("record_incident returns dict", isinstance(record, dict))
    check("Record has timestamp", "timestamp" in record)
    check("Record has incident", record["incident"] == inc)
    check("Record has classification", record["classification"]["level"] == "P2")
    
    # --- Incidents file exists and is valid JSONL ---
    check("incidents.jsonl exists", os.path.exists(INCIDENTS_FILE))
    with open(INCIDENTS_FILE) as f:
        lines = [l for l in f.readlines() if l.strip()]
    check("incidents.jsonl has entries", len(lines) >= 1)
    valid = True
    for line in lines:
        try:
            json.loads(line)
        except json.JSONDecodeError:
            valid = False
            break
    check("All incidents.jsonl entries valid JSON", valid)
    
    # --- Alerts file has P1 entry ---
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE) as f:
            alert_lines = [l for l in f.readlines() if l.strip()]
        check("incident-alerts.jsonl has entries", len(alert_lines) >= 1)
        last_alert = json.loads(alert_lines[-1])
        check("Last alert is P1", last_alert.get("level") == "P1")
    else:
        check("incident-alerts.jsonl created", False)
    
    # --- Summary ---
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n=== RESULT: {passed}/{total} PASS ===")
    return passed == total


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        success = selftest()
        sys.exit(0 if success else 1)
    elif "--classify" in sys.argv:
        idx = sys.argv.index("--classify")
        if idx + 1 < len(sys.argv):
            inc = json.loads(sys.argv[idx + 1])
            cls = classify(inc)
            record = record_incident(inc, cls)
            alert = send_alert(cls, inc)
            print(json.dumps({"classification": cls, "alert": alert}, indent=2))
        else:
            print("Usage: --classify '{json}'")
            sys.exit(1)
    else:
        print(__doc__)
