#!/usr/bin/env python3
"""verify_onboarding.py — Companion script for agent-onboarding-playbook.md.
Validates that every agent in agents.json has the required onboarding fields.
Exit: 0=all onboarded, 1=missing fields found.
"""
import json, sys
from pathlib import Path

REQUIRED_FIELDS = ["name", "role", "host", "model_id", "status"]

def main():
    agents_path = Path("agents.json")
    if not agents_path.exists():
        print(json.dumps({"status": "FAIL", "error": "agents.json not found"}))
        sys.exit(1)
    
    try:
        data = json.loads(agents_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "FAIL", "error": f"JSON parse error: {e}"}))
        sys.exit(1)
    
    agents = data if isinstance(data, list) else data.get("agents", [])
    issues = []
    for agent in agents:
        name = agent.get("name", "<unnamed>")
        missing = [f for f in REQUIRED_FIELDS if f not in agent or not agent[f]]
        if missing:
            issues.append({"agent": name, "missing": missing})
    
    if issues:
        print(json.dumps({"status": "FAIL", "issues": issues}, indent=2))
        sys.exit(1)
    print(json.dumps({"status": "OK", "agents_checked": len(agents)}))
    sys.exit(0)

if __name__ == "__main__":
    main()
