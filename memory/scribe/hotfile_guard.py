import os, re, json, hashlib
from datetime import datetime
from pathlib import Path

"""Hot-file auto-trim + drift guard (Scribe goal #3).
Run each turn: enforces MEMORY.md <40 lines with lossless archive,
detects MEMORY<->TODO goal-line drift.
"""

# --- Config ---
MEMORY_MD = Path("MEMORY.md")
TODO_MD = Path("TODO.md")
ARCHIVE_DIR = Path("memory/scribe/archive")
MAX_LINES = 40
REPORT_FILE = Path("memory/scribe/hotfile-guard-report.json")

def extract_goal_section(memory_text):
    """Extract the GOAL section from MEMORY.md."""
    lines = memory_text.splitlines()
    in_goal = False
    goal_lines = []
    for line in lines:
        if line.startswith("## GOAL"):
            in_goal = True
            continue
        elif in_goal and line.startswith("## "):
            break
        elif in_goal:
            goal_lines.append(line)
    return "\n".join(goal_lines).strip()

def extract_todo_live_plan(todo_text):
    """Extract the live plan from TODO.md."""
    lines = todo_text.splitlines()
    in_plan = False
    plan_lines = []
    for line in lines:
        if line.startswith("## CYCLE") or line.startswith("## LIVE PLAN"):
            in_plan = True
            continue
        elif in_plan and line.startswith("## "):
            break
        elif in_plan:
            plan_lines.append(line)
    return "\n".join(plan_lines).strip()

def normalize_for_compare(text):
    """Normalize for drift comparison."""
    text = re.sub(r'\d{4}-\d{2}-\d{2}', '', text)
    text = re.sub(r'\d{1,2}:\d{2}', '', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text

def extract_key_facts(text):
    """Extract key facts: cycle numbers, goal counts, status words."""
    facts = set()
    for m in re.finditer(r'cycle[\s_-]*(\d+)', text, re.I):
        facts.add(f"cycle{m.group(1)}")
    for m in re.finditer(r'(\d+)/\d+', text):
        facts.add(f"goals:{m.group(1)}")
    for kw in ['OPENED', 'CLOSED', 'PENDING', 'LIVE', 'BLOCKED']:
        if kw in text.upper():
            facts.add(kw)
    return facts

def detect_drift(memory_text, todo_text):
    """Compare key facts between MEMORY.md GOAL and TODO.md live plan."""
    mem_goal = extract_goal_section(memory_text)
    todo_plan = extract_todo_live_plan(todo_text)
    
    if not mem_goal and not todo_plan:
        return {"drift": False, "note": "Both sections empty or missing"}
    if not mem_goal:
        return {"drift": True, "detail": "MEMORY.md GOAL section is empty but TODO.md has a live plan"}
    if not todo_plan:
        return {"drift": True, "detail": "TODO.md live plan is empty but MEMORY.md has a GOAL section"}
    
    mem_facts = extract_key_facts(mem_goal)
    todo_facts = extract_key_facts(todo_plan)
    
    missing_in_todo = mem_facts - todo_facts
    missing_in_mem = todo_facts - mem_facts
    
    drift = bool(missing_in_todo or missing_in_mem)
    return {
        "drift": drift,
        "missing_in_todo": sorted(missing_in_todo),
        "missing_in_memory": sorted(missing_in_mem),
        "mem_facts": sorted(mem_facts),
        "todo_facts": sorted(todo_facts)
    }

def trim_hot_notes(memory_text, max_lines=MAX_LINES):
    """If MEMORY.md exceeds max_lines, move oldest Hot Notes to archive."""
    lines = memory_text.splitlines()
    if len(lines) <= max_lines:
        return memory_text, []
    
    in_hot_notes = False
    hot_note_indices = []
    for i, line in enumerate(lines):
        if line.startswith("## Hot Notes"):
            in_hot_notes = True
            continue
        elif in_hot_notes and line.startswith("## "):
            break
        elif in_hot_notes and line.strip().startswith("- "):
            hot_note_indices.append(i)
    
    if not hot_note_indices:
        return memory_text, []
    
    excess = len(lines) - max_lines + 2
    to_remove = min(excess, len(hot_note_indices))
    
    if to_remove <= 0:
        return memory_text, []
    
    indices_to_remove = hot_note_indices[-to_remove:]
    moved_entries = [lines[i] for i in indices_to_remove]
    new_lines = [l for i, l in enumerate(lines) if i not in set(indices_to_remove)]
    
    return "\n".join(new_lines) + "\n", moved_entries

def main():
    results = {
        "timestamp": datetime.now().isoformat(),
        "memory_md_lines": 0,
        "trim_action": None,
        "drift_report": None,
        "status": "PASS"
    }
    
    memory_text = MEMORY_MD.read_text(encoding="utf-8") if MEMORY_MD.exists() else ""
    todo_text = TODO_MD.read_text(encoding="utf-8") if TODO_MD.exists() else ""
    
    results["memory_md_lines"] = len(memory_text.splitlines())
    
    if results["memory_md_lines"] > MAX_LINES:
        new_text, moved = trim_hot_notes(memory_text)
        if moved:
            ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
            archive_path = ARCHIVE_DIR / f"hot-notes-trimmed-{datetime.now().strftime('%Y-%m-%d')}.md"
            with open(archive_path, "a", encoding="utf-8") as f:
                f.write(f"\n## Trimmed {datetime.now().isoformat()}\n")
                for entry in moved:
                    f.write(entry + "\n")
            MEMORY_MD.write_text(new_text, encoding="utf-8")
            results["trim_action"] = {
                "lines_before": results["memory_md_lines"],
                "lines_after": len(new_text.splitlines()),
                "entries_moved": len(moved),
                "archive_path": str(archive_path)
            }
            memory_text = new_text
        else:
            results["trim_action"] = {"note": "Exceeded limit but no hot notes to trim"}
    else:
        results["trim_action"] = {"within_limit": True, "lines": results["memory_md_lines"], "limit": MAX_LINES}
    
    results["drift_report"] = detect_drift(memory_text, todo_text)
    if results["drift_report"]["drift"]:
        results["status"] = "DRIFT_DETECTED"
    
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"MEMORY.md: {results['memory_md_lines']} lines (limit {MAX_LINES})")
    if results["trim_action"].get("entries_moved"):
        print(f"  TRIMMED: moved {results['trim_action']['entries_moved']} entries -> {results['trim_action']['archive_path']}")
    else:
        print(f"  Within limit or no trim needed")
    
    drift = results["drift_report"]
    if drift["drift"]:
        print(f"  DRIFT DETECTED:")
        for m in drift.get("missing_in_todo", []):
            print(f"    In MEMORY not TODO: {m}")
        for m in drift.get("missing_in_memory", []):
            print(f"    In TODO not MEMORY: {m}")
    else:
        print(f"  No drift detected (key facts aligned)")
    
    print(f"\nStatus: {results['status']}")

if __name__ == "__main__":
    main()
