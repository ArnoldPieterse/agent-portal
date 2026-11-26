#!/usr/bin/env python3
"""
Goal-Set Drift Detector (Scribe Goal #6, Cycle 26)

Compares each cycle's actual goal set vs the previous; flags:
- STUCK: goals re-proposed but never advanced (same signature >=2 consecutive cycles, not in closed_topics)
- DROPPED-UNCLOSED: goals that silently disappeared (present in previous but absent in current, no closure record)

Usage: python memory/scribe/goalset_drift.py [--lane scribe] [--cycles N]
Output: memory/scribe/goalset-drift.jsonl
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

GOALS_DIR = Path("memory/goals")
ARCHIVE_DIR = GOALS_DIR / "archive"
CLOSED_TOPICS = GOALS_DIR / "closed_topics.json"
OUTPUT_FILE = Path("memory/scribe/goalset-drift.jsonl")

DEFAULT_LANE = "scribe"
DEFAULT_CYCLES = 5  # compare last N cycles


def extract_goal_signatures(filepath):
    """Extract goal title signatures from a goals file.
    
    Returns list of (goal_num, title) tuples.
    A 'signature' is the bold title text: **Title Here**
    """
    if not filepath.exists():
        return []
    text = filepath.read_text(encoding="utf-8")
    goals = []
    # Match lines like: 1. **Goal Title** - description...
    for m in re.finditer(r"^(\d+)\.\s+\*\*(.+?)\*\*", text, re.MULTILINE):
        num = int(m.group(1))
        title = m.group(2).strip()
        goals.append((num, title))
    return goals


def extract_date_from_filename(filename):
    """Extract a sortable date from a goal filename. Returns (date_str, cycle_num) or ('', 0)."""
    import re
    # Pattern: scribe-2026-11-26-cycle25.md or scribe-cycle14-2026-11-24.md
    m = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    date_str = m.group(1) if m else ''
    m2 = re.search(r'cycle(\d+)', filename, re.IGNORECASE)
    cycle_num = int(m2.group(1)) if m2 else 0
    return date_str, cycle_num


def get_cycle_files(lane):
    """Get sorted list of (filepath, label) for a lane's goal files across cycles.
    
    Filters out test files and sorts chronologically by embedded date.
    """
    files = []
    
    # Current goals file
    current = GOALS_DIR / f"{lane}.md"
    if current.exists():
        files.append((current, "current", "9999-99-99", 999))
    
    # Archived files
    if ARCHIVE_DIR.exists():
        for f in ARCHIVE_DIR.iterdir():
            if not f.is_file():
                continue
            if not (f.name.startswith(f"{lane}-") or f.name.startswith(f"{lane}_")):
                continue
            # Filter out test files
            if 'test' in f.name.lower() or '_15.md' == f.name[-6:]:
                continue
            date_str, cycle_num = extract_date_from_filename(f.name)
            if not date_str:
                continue  # skip files without a parseable date
            files.append((f, f.name, date_str, cycle_num))
    
    # Sort by (date, cycle_num) chronologically
    files.sort(key=lambda x: (x[2], x[3]))
    
    # Return just (filepath, label)
    return [(f, label) for f, label, _, _ in files]


def is_closed(title, closed_topics):
    """Check if a goal title matches any entry in closed_topics.json."""
    title_lower = title.lower()
    for entry in closed_topics:
        # Entries can be strings or dicts
        if isinstance(entry, str):
            if title_lower in entry.lower() or entry.lower() in title_lower:
                return True
        elif isinstance(entry, dict):
            entry_text = json.dumps(entry).lower()
            if title_lower in entry_text:
                return True
    return False


def was_reached_in_file(filepath, title):
    """Check if a goal was marked REACHED (✅) in its source file."""
    if not filepath.exists():
        return False
    text = filepath.read_text(encoding="utf-8")
    for line in text.split('\n'):
        if title in line and ('REACHED' in line or '\u2705' in line):
            return True
    return False


def detect_drift(lane=DEFAULT_LANE, max_cycles=DEFAULT_CYCLES):
    """Run drift detection across consecutive cycles."""
    # Load closed topics
    closed_topics = []
    if CLOSED_TOPICS.exists():
        try:
            closed_topics = json.loads(CLOSED_TOPICS.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Get cycle files
    cycle_files = get_cycle_files(lane)
    if len(cycle_files) < 2:
        print(f"[goalset_drift] Need >=2 goal files for {lane}, found {len(cycle_files)}")
        return []
    
    # Take last N+1 (need pairs to compare)
    relevant = cycle_files[-(max_cycles + 1):]
    print(f"[goalset_drift] Comparing {len(relevant)} cycles for lane '{lane}'")
    
    drifts = []
    prev_goals = None
    prev_label = None
    prev_filepath = None
    
    for filepath, label in relevant:
        goals = extract_goal_signatures(filepath)
        current_titles = set(t for _, t in goals)
        
        if prev_goals is not None:
            prev_titles = set(t for _, t in prev_goals)
            
            # STUCK: in both previous and current, not closed
            for title in current_titles & prev_titles:
                if not is_closed(title, closed_topics):
                    drifts.append({
                        "cycle": label,
                        "goal_sig": title,
                        "status": "stuck",
                        "detail": f"Present in both {prev_label} and {label}, not in closed_topics"
                    })
            
            # DROPPED-UNCLOSED: in previous but not current, not closed, not reached
            for title in prev_titles - current_titles:
                if not is_closed(title, closed_topics) and not was_reached_in_file(prev_filepath, title):
                    drifts.append({
                        "cycle": label,
                        "goal_sig": title,
                        "status": "dropped-unclosed",
                        "detail": f"In {prev_label} but absent from {label}, no closure record"
                    })
        
        prev_goals = goals
        prev_label = label
        prev_filepath = filepath
    
    return drifts


def main():
    lane = DEFAULT_LANE
    max_cycles = DEFAULT_CYCLES
    
    # Parse args
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--lane" and i + 1 < len(args):
            lane = args[i + 1]
        elif arg == "--cycles" and i + 1 < len(args):
            max_cycles = int(args[i + 1])
    
    print(f"[goalset_drift] Lane: {lane}, cycles: {max_cycles}")
    
    drifts = detect_drift(lane, max_cycles)
    
    # Add timestamp
    ts = datetime.utcnow().isoformat()
    for d in drifts:
        d["detected_at"] = ts
    
    # Write to output (append mode)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for d in drifts:
            f.write(json.dumps(d) + "\n")
    
    # Summary
    stuck = [d for d in drifts if d["status"] == "stuck"]
    dropped = [d for d in drifts if d["status"] == "dropped-unclosed"]
    print(f"[goalset_drift] Found {len(drifts)} drift events: {len(stuck)} stuck, {len(dropped)} dropped-unclosed")
    for d in drifts:
        print(f"  [{d['status']}] {d['goal_sig'][:60]} ({d['cycle']})")
    
    if not drifts:
        print("[goalset_drift] No drift detected - clean transition")
    
    print(f"[goalset_drift] Output: {OUTPUT_FILE}")
    print("[goalset_drift] DONE")


if __name__ == "__main__":
    main()
