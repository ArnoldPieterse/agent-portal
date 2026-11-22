"""Cross-Agent Handoff Summarizer (Scribe Goal #3)

When a task is re-routed between agents, auto-generate a context handoff document:
- Original task
- Progress made
- What's remaining
- Gotchas discovered

Scans memory/ops/left-*.md (departed agent notes), blockers.md, and TODO.md.
Writes to memory/ops/handoffs/.

Usage: python memory/scribe/handoff_summary.py
"""
import os, json, re, datetime

def get_today():
    return datetime.date.today().isoformat()

def read_file(path):
    if not os.path.exists(path):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def scan_left_files():
    """Scan memory/ops/left-*.md for departed agent handoffs."""
    handoffs = []
    ops_dir = "memory/ops"
    if not os.path.isdir(ops_dir):
        return handoffs
    for fname in sorted(os.listdir(ops_dir)):
        if not fname.startswith("left-") or not fname.endswith(".md"):
            continue
        agent = fname[5:-3]
        path = os.path.join(ops_dir, fname)
        content = read_file(path)
        goals = []
        for line in content.split('\n'):
            m = re.match(rf'^\s*{re.escape(agent)}\s*\|\s*(.+)', line)
            if m:
                goals.append(m.group(1).strip())
        date_match = re.search(r'Last updated\s+([\d\-]+)', content)
        date = date_match.group(1) if date_match else get_today()
        handoffs.append({
            "agent": agent,
            "date": date,
            "source": f"memory/ops/{fname}",
            "goals": goals,
            "type": "departure",
            "context": content[:500]
        })
    return handoffs

def scan_blockers_for_reassignment():
    """Scan blockers.md for any reassignment markers."""
    content = read_file("memory/ops/blockers.md")
    reassignments = []
    for line in content.split('\n'):
        if re.search(r'(reassign|now owned|moved to|transferred)', line, re.IGNORECASE):
            reassignments.append(line.strip())
    return reassignments

def scan_todo_for_ownership():
    """Scan TODO.md for goal ownership annotations."""
    content = read_file("TODO.md")
    ownership_notes = []
    for line in content.split('\n'):
        if re.search(r'(owner|assigned to|now with)', line, re.IGNORECASE):
            ownership_notes.append(line.strip())
    return ownership_notes

def generate_handoff_doc(handoff):
    """Generate a structured handoff document from a detected re-routing event."""
    agent = handoff["agent"]
    date = handoff["date"]
    goals = handoff["goals"]
    
    todo = read_file("TODO.md")
    completed = []
    remaining = []
    for goal in goals:
        snippet = goal[:50].lower()
        if snippet and snippet in todo.lower():
            idx = todo.lower().find(snippet)
            window = todo[max(0, idx-100):idx+200]
            if re.search(r'(verified|done|complete|closed)', window, re.IGNORECASE):
                completed.append(goal)
            else:
                remaining.append(goal)
        else:
            remaining.append(goal)
    
    blockers = read_file("memory/ops/blockers.md")
    gotchas = []
    for line in blockers.split('\n'):
        if agent.lower() in line.lower() and re.search(r'(block|error|fail|wall)', line, re.IGNORECASE):
            gotchas.append(line.strip())
    
    doc_lines = [
        f"# HANDOFF: {agent.capitalize()} \u2014 Open goals at departure",
        f"**From:** {agent} (departed/unreachable)",
        f"**To:** next available agent (Orchestrator to assign)",
        f"**Date:** {date}",
        f"**Source:** {handoff['source']}",
        f"**Class:** departure-handoff",
        "",
        "## Original Task(s)",
    ]
    if goals:
        for i, g in enumerate(goals, 1):
            doc_lines.append(f"{i}. {g}")
    else:
        doc_lines.append("(No specific goals extracted \u2014 see source file)")
    
    doc_lines += ["", "## Progress Made"]
    if completed:
        for g in completed:
            doc_lines.append(f"- [x] {g[:80]}")
    else:
        doc_lines.append("- No completion evidence found in TODO.md for these goals.")
    
    doc_lines += ["", "## Remaining Work"]
    if remaining:
        for g in remaining:
            doc_lines.append(f"- [ ] {g[:100]}")
    else:
        doc_lines.append("- All tracked goals appear complete.")
    
    doc_lines += ["", "## Gotchas / Known Issues"]
    if gotchas:
        for g in gotchas[:5]:
            doc_lines.append(f"- {g[:120]}")
    else:
        doc_lines.append("- No agent-specific blockers found in memory/ops/blockers.md.")
    
    doc_lines += ["", "## Status", "[OPEN \u2014 awaiting reassignment]"]
    
    return "\n".join(doc_lines)

def main():
    today = get_today()
    os.makedirs("memory/ops/handoffs", exist_ok=True)
    
    left_handoffs = scan_left_files()
    blocker_reassigns = scan_blockers_for_reassignment()
    todo_ownership = scan_todo_for_ownership()
    
    print(f"Found {len(left_handoffs)} departure handoffs")
    print(f"Found {len(blocker_reassigns)} blocker reassignments")
    print(f"Found {len(todo_ownership)} TODO ownership notes")
    
    generated = 0
    for h in left_handoffs:
        safe_name = f"{h['agent']}-{h['date'].replace('-','')}.md"
        out_path = os.path.join("memory/ops/handoffs", safe_name)
        if os.path.exists(out_path):
            print(f"  SKIP (exists): {safe_name}")
            continue
        doc = generate_handoff_doc(h)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(doc)
        generated += 1
        print(f"  WROTE: memory/ops/handoffs/{safe_name} ({len(doc)} bytes)")
    
    print(f"\nGenerated {generated} new handoff documents.")
    if blocker_reassigns:
        print("Blocker reassignments detected:")
        for r in blocker_reassigns[:5]:
            print(f"  {r[:100]}")
    
    return generated

if __name__ == "__main__":
    main()
