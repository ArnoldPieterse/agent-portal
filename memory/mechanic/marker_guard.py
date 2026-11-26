#!/usr/bin/env python3
"""marker_guard.py - Self-healing for (verified:) markers in goal files.

Reads goal_ledger.json; for each lane with reached+evidenced goals, checks if
the (verified:) marker exists on the corresponding numbered line in the goal file.
If missing, appends it. Logs actions to memory/ops/marker-guard-log.jsonl.

Serves: Fleet Autonomy Convergence (self-healing state tracking).
Usage: python memory/mechanic/marker_guard.py [--dry-run]
"""
import json, pathlib, sys, datetime, re

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
LEDGER = ROOT / "goal_ledger.json"
LOG_FILE = ROOT / "memory" / "ops" / "marker-guard-log.jsonl"

def get_markers_for_lane(lane_data):
    """Extract (goal_num, marker) pairs from ledger data for a lane."""
    markers = []
    for idx, g in enumerate(lane_data.get("goals", []), 1):
        if g.get("status") == "reached" and g.get("evidence"):
            text = g.get("text", "")
            if "(verified:" in text:
                start = text.index("(verified:")
                end = text.rindex(")") + 1
                markers.append((idx, text[start:end]))
    return markers

def fix_lane(lane, markers, dry_run=False):
    """Re-apply missing (verified:) markers to correct numbered lines."""
    goal_file = ROOT / "memory" / "goals" / f"{lane}.md"
    if not goal_file.exists():
        return 0
    content = goal_file.read_text(encoding="utf-8")
    lines = content.split("\n")
    fixed = 0
    
    for num, marker in markers:
        if marker in content:
            continue  # already present
        
        # Find the line starting with "N. " (where N is goal number)
        pattern = rf"^{num}\.\s"
        inserted = False
        for i, line in enumerate(lines):
            if re.match(pattern, line.strip()) and "(verified:" not in line:
                lines[i] = line.rstrip() + f" {marker}"
                inserted = True
                break
        
        if not inserted:
            # Fallback: find any numbered line that doesn't have the marker yet
            # and whose title words overlap with the marker context
            key_words = re.findall(r"[A-Za-z]{4,}", marker)[:3]
            for i, line in enumerate(lines):
                if "(verified:" in line:
                    continue
                if re.match(rf"^{num}\.\s", line.strip()):
                    lines[i] = line.rstrip() + f" {marker}"
                    inserted = True
                    break
        
        if inserted:
            fixed += 1
    
    if fixed and not dry_run:
        goal_file.write_text("\n".join(lines), encoding="utf-8")
    return fixed

def run(dry_run=False):
    if not LEDGER.exists():
        print("LEDGER NOT FOUND:", LEDGER)
        return 1
    
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    total_missing = 0
    actions = []
    
    for lane, info in sorted(data.get("agents", {}).items()):
        markers = get_markers_for_lane(info)
        if not markers:
            continue
        goal_file = ROOT / "memory" / "goals" / f"{lane}.md"
        if not goal_file.exists():
            continue
        content = goal_file.read_text(encoding="utf-8")
        missing = [(n, m) for n, m in markers if m not in content]
        if missing:
            total_missing += len(missing)
            n_fixed = fix_lane(lane, missing, dry_run=dry_run)
            actions.append({"lane": lane, "missing": len(missing), "fixed": n_fixed})
    
    entry = {
        "ts": datetime.datetime.now().isoformat(),
        "lanes_checked": sum(1 for l in data.get("agents", {}) if (ROOT/"memory"/"goals"/f"{l}.md").exists()),
        "total_missing": total_missing,
        "actions": actions,
        "dry_run": dry_run
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    
    tag = "DRY-RUN" if dry_run else "FIXED"
    print(f"[marker-guard] {tag}: {total_missing} markers missing across lanes")
    for a in actions:
        print(f"  - {a['lane']}: {a['missing']} missing, {a['fixed']} re-applied")
    return 0

if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    sys.exit(run(dry_run=dry))
