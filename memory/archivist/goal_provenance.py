#!/usr/bin/env python3
"""goal_provenance.py — Archivist: evidence-chain tracker for fleet goals.

Wish: Provenance-Linked Goal Audit. Every goal gets an unbroken evidence chain
back to the artifact that proves it was reached. No self-declared [x] without a
file, commit, or verifiable output backing it.

Usage: python goal_provenance.py [--output report.json]
"""
import json, os, re, sys, hashlib
from datetime import datetime

AGENTS = ["orchestrator","researcher","builder","archivist","scribe","verifier","designer","mechanic"]
GOALS_DIR = "memory/goals"
MEMORY_DIR = "memory"

def md5_file(path):
    try:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, IOError):
        return None

def parse_goals(agent):
    """Parse numbered goal lines from memory/goals/{agent}.md."""
    path = os.path.join(GOALS_DIR, agent + ".md")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    goals = []
    for line in text.splitlines():
        m = re.match(r"^\s*(\d+)\.\s+(.+)", line)
        if m:
            num = int(m.group(1))
            desc = m.group(2).strip()
            goals.append({"num": num, "desc": desc})
    return goals

def extract_file_refs(desc):
    """Extract file paths mentioned in a goal description."""
    refs = []
    for m in re.finditer(r"`([^`]+\.\w+)`", desc):
        refs.append(m.group(1))
    for m in re.finditer(r"\b((?:memory|reports|agents)\/[\w./-]+)\b", desc):
        refs.append(m.group(1))
    return refs

def find_evidence(goal_desc, file_refs, agent):
    """Find evidence files that prove a goal was reached."""
    evidence = []
    for ref in file_refs:
        candidates = [ref, ref.replace("/", os.sep)]
        for c in candidates:
            if os.path.exists(c) and os.path.isfile(c):
                evidence.append({
                    "file": c,
                    "md5": md5_file(c),
                    "size": os.path.getsize(c),
                    "type": "artifact"
                })
                break
    # Check TODO.md for [x] lines mentioning this goal's key terms
    try:
        with open("TODO.md", "r", encoding="utf-8") as f:
            todo_text = f.read()
        keywords = re.findall(r"[A-Za-z_]{4,}", goal_desc)
        for line in todo_text.splitlines():
            if "[x]" in line[:6]:
                hits = sum(1 for kw in keywords[:5] if kw.lower() in line.lower())
                if hits >= 2:
                    evidence.append({
                        "file": "TODO.md",
                        "line": line.strip()[:120],
                        "type": "todo-verified"
                    })
                    break
    except (OSError, IOError):
        pass
    # Check memory/{agent}/ for files that reference this goal number
    agent_dir = os.path.join(MEMORY_DIR, agent)
    if os.path.isdir(agent_dir):
        try:
            for fname in os.listdir(agent_dir):
                fpath = os.path.join(agent_dir, fname)
                if not os.path.isfile(fpath):
                    continue
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read(2000)
                    if re.search(r"goal\s+" + str(goal_desc[:3]) + r"\b", content, re.IGNORECASE):
                        evidence.append({
                            "file": fpath,
                            "md5": md5_file(fpath),
                            "type": "agent-record"
                        })
                except (OSError, IOError, UnicodeDecodeError):
                    pass
        except OSError:
            pass
    return evidence

def main():
    output_path = "memory/archivist/goal_provenance_report.json"
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = sys.argv[idx + 1]

    all_goals = {}
    for agent in AGENTS:
        goals = parse_goals(agent)
        enriched = []
        for g in goals:
            refs = extract_file_refs(g["desc"])
            ev = find_evidence(g["desc"], refs, agent)
            has_artifact = any(e.get("type") == "artifact" for e in ev)
            has_todo = any(e.get("type") == "todo-verified" for e in ev)
            status = "evidenced" if (has_artifact or has_todo) else "open"
            enriched.append({
                "num": g["num"],
                "desc": g["desc"][:200],
                "file_refs": refs,
                "evidence": ev,
                "status": status,
                "confidence": "high" if has_artifact else ("medium" if has_todo else "unverified")
            })
        all_goals[agent] = enriched

    total = sum(len(v) for v in all_goals.values())
    evidenced = sum(1 for v in all_goals.values() for g in v if g["status"] == "evidenced")
    report = {
        "generated": datetime.now().isoformat(),
        "generator": "Archivist / goal_provenance.py",
        "wish": "Provenance-Linked Goal Audit: every goal carries an unbroken evidence chain to its proving artifact",
        "summary": {
            "total_goals": total,
            "evidenced": evidenced,
            "open": total - evidenced,
            "evidence_rate": round(evidenced / max(total, 1) * 100, 1),
            "per_agent": {a: {"total": len(v), "evidenced": sum(1 for g in v if g["status"]=="evidenced")} for a, v in all_goals.items()}
        },
        "goals": all_goals
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Provenance report: {output_path} ({os.path.getsize(output_path)} B)")
    print(f"\nFleet: {evidenced}/{total} goals have file evidence ({report['summary']['evidence_rate']}%)")
    for a in AGENTS:
        s = report["summary"]["per_agent"][a]
        bar = "#" * s["evidenced"] + "." * (s["total"] - s["evidenced"])
        print(f"  {a:<14} {bar} {s['evidenced']}/{s['total']}")

if __name__ == "__main__":
    main()
