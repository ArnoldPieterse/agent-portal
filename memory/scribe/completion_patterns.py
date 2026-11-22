#!/usr/bin/env python3
"""Goal Completion Pattern Analysis - analyzes completed goals across cycles."""
import os, re, json
from datetime import datetime

KNOWN_AGENTS = ["orchestrator", "researcher", "builder", "verifier",
                "designer", "archivist", "mechanic", "scribe"]

def parse_goals():
    """Parse all goal files (current + archived)."""
    goals = []
    for root, dirs, files in os.walk("memory/goals"):
        for fn in files:
            if not fn.endswith(".md") or fn.startswith("_"):
                continue
            gpath = os.path.join(root, fn)
            m = re.match(r"^([a-z]+)-", fn)
            agent = m.group(1) if m else None
            if agent not in KNOWN_AGENTS:
                continue
            try:
                with open(gpath, encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except Exception:
                continue
            for line in content.split("\n"):
                gm = re.match(r"^\d+\. \*\*(.+?)\*\*", line)
                if not gm:
                    continue
                title = gm.group(1).strip()
                verified = "(verified:" in line
                gtype = classify(title)
                goals.append({"agent": agent, "title": title,
                              "type": gtype, "verified": verified,
                              "file": gpath})
    return goals

def classify(title):
    t = title.lower()
    if any(w in t for w in ["test", "verify", "audit", "check", "validate"]):
        return "verify"
    if any(w in t for w in ["build", "create", "implement", "frontend", "widget", "script", "automation"]):
        return "build"
    if any(w in t for w in ["research", "investigate", "find", "analyze", "analysis"]):
        return "research"
    if any(w in t for w in ["design", "layout", "ux", "visual"]):
        return "design"
    if any(w in t for w in ["monitor", "daemon", "maintenance", "recovery", "lifecycle"]):
        return "ops"
    return "other"

def main():
    goals = parse_goals()
    total = len(goals)
    completed = sum(1 for g in goals if g["verified"])
    
    # By agent
    by_agent = {}
    for g in goals:
        a = g["agent"]
        if a not in by_agent:
            by_agent[a] = {"total": 0, "done": 0}
        by_agent[a]["total"] += 1
        if g["verified"]:
            by_agent[a]["done"] += 1
    
    # By type
    by_type = {}
    for g in goals:
        t = g["type"]
        if t not in by_type:
            by_type[t] = {"total": 0, "done": 0}
        by_type[t]["total"] += 1
        if g["verified"]:
            by_type[t]["done"] += 1
    
    # Generate report
    lines = [f"# Goal Completion Pattern Analysis", f"",
             f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", f"",
             f"## Summary", f"",
             f"- Total goals tracked: {total}",
             f"- Completed (verified): {completed} ({100*completed//max(total,1)}%)",
             f"- Agents: {len(by_agent)}", f"",
             f"## Completion Rate by Agent", f""]
    for agent in sorted(by_agent, key=lambda a: -by_agent[a]["done"]/max(by_agent[a]["total"],1)):
        d = by_agent[agent]
        rate = 100*d["done"]/max(d["total"],1)
        lines.append(f"- {agent}: {d['done']}/{d['total']} ({rate:.0f}%)")
    
    lines += ["", "## Completion Rate by Goal Type", ""]
    for t in sorted(by_type, key=lambda x: -by_type[x]["done"]/max(by_type[x]["total"],1)):
        d = by_type[t]
        rate = 100*d["done"]/max(d["total"],1)
        lines.append(f"- {t}: {d['done']}/{d['total']} ({rate:.0f}%)")
    
    # Insights
    lines += ["", "## Key Insights", ""]
    best_agent = max(by_agent, key=lambda a: by_agent[a]["done"]/max(by_agent[a]["total"],1))
    worst_type = min(by_type, key=lambda t: by_type[t]["done"]/max(by_type[t]["total"],1))
    lines.append(f"1. Highest completion agent: {best_agent} "
                 f"({by_agent[best_agent]['done']}/{by_agent[best_agent]['total']})")
    lines.append(f"2. Lowest completion type: {worst_type} "
                 f"({by_type[worst_type]['done']}/{by_type[worst_type]['total']})")
    top_types = sorted(by_type.items(), key=lambda x: -x[1]["done"])[:3]
    lines.append(f"3. Most completed types: {', '.join(f'{t}({d['done']})' for t,d in top_types)}")
    
    report = "\n".join(lines)
    
    # Write output
    os.makedirs("memory/synthesis", exist_ok=True)
    out = f"memory/synthesis/completion-patterns-{datetime.now().strftime('%Y-%m-%d')}.md"
    with open(out, "w") as fh:
        fh.write(report)
    
    print(report)
    print(f"\nWrote: {out}")

if __name__ == "__main__":
    main()
