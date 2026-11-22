"""Decision Log Integrity Audit.

Verifies memory/ops/decision-log.jsonl meets structural and logical invariants:
  T1: Every entry has required fields (ts, agent, type)
  T2: Timestamps are monotonically non-decreasing
  T3: Agent names are consistent (case-normalized set is small)
  T4: playbook_complete entries have matching step counts vs their preceding steps
  T5: Rollback entries reference valid step numbers from the same runbook session

Exit 0 = all pass, 1 = violations found. Writes report to decision_log_audit.json.
"""
import json, sys, pathlib
from datetime import datetime

LOG = pathlib.Path("memory/ops/decision-log.jsonl")
REPORT = pathlib.Path("memory/verifier/decision_log_audit.json")

def parse_ts(s):
    return datetime.fromisoformat(s)

def audit():
    if not LOG.exists():
        return {"status": "FAIL", "reason": "decision-log.jsonl not found"}
    
    lines = LOG.read_text(encoding="utf-8").strip().split("\n")
    entries = []
    issues = []
    
    for i, line in enumerate(lines):
        try:
            e = json.loads(line)
            entries.append(e)
        except json.JSONDecodeError as ex:
            issues.append({"test": "T1", "line": i, "detail": f"invalid JSON: {ex}"})
    
    # T1: required fields
    for i, e in enumerate(entries):
        for field in ("ts", "agent", "type"):
            if field not in e:
                issues.append({"test": "T1", "line": i, "detail": f"missing '{field}'"})
    
    # T2: monotonic timestamps
    ts_list = [parse_ts(e["ts"]) for e in entries if "ts" in e]
    for i in range(1, len(ts_list)):
        if ts_list[i] < ts_list[i-1]:
            issues.append({"test": "T2", "line": i, "detail": f"ts {ts_list[i].isoformat()} < prev {ts_list[i-1].isoformat()}"})
    
    # T3: agent consistency (case-normalized)
    agents = set(e.get("agent","").lower() for e in entries if "agent" in e)
    if len(agents) > 8:
        issues.append({"test": "T3", "line": -1, "detail": f"{len(agents)} distinct agents: {agents}"})
    
    # T4: playbook_complete step count matches
    for i, e in enumerate(entries):
        if e.get("type") == "playbook_complete":
            # Count preceding playbook_step entries for same runbook since last complete/dry_run
            runbook = e.get("runbook","")
            steps_before = 0
            for j in range(i-1, -1, -1):
                if entries[j].get("type") == "playbook_step" and entries[j].get("runbook") == runbook:
                    steps_before += 1
                elif entries[j].get("type") in ("playbook_complete", "playbook_dry_run"):
                    break
            declared = e.get("steps_total", -1)
            if steps_before != declared:
                issues.append({"test": "T4", "line": i, "detail": f"declared {declared} steps but found {steps_before} preceding step entries"})
    
    # T5: rollback references valid step
    for i, e in enumerate(entries):
        if e.get("type") == "playbook_rollback":
            step = e.get("step", -1)
            runbook = e.get("runbook","")
            # Find preceding steps for this runbook
            valid_steps = set()
            for j in range(i-1, -1, -1):
                if entries[j].get("type") == "playbook_step" and entries[j].get("runbook") == runbook:
                    valid_steps.add(entries[j].get("step"))
                elif entries[j].get("type") in ("playbook_complete", "playbook_dry_run"):
                    break
            if step not in valid_steps:
                issues.append({"test": "T5", "line": i, "detail": f"rollback references step {step} not found in session (valid: {sorted(valid_steps)})"})
    
    result = {
        "status": "PASS" if not issues else "FAIL",
        "entries_total": len(entries),
        "issues_count": len(issues),
        "issues": issues,
        "agents_seen": sorted(agents),
        "time_span": [ts_list[0].isoformat(), ts_list[-1].isoformat()] if ts_list else [],
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

if __name__ == "__main__":
    r = audit()
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["status"] == "PASS" else 1)
