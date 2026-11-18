#!/usr/bin/env python3
"""Auto-scan memory files for unresolved questions/items not yet in open-items.md.

Usage: python memory/scribe/open_items_scan.py [--report]

Scans:
  - memory/goals/*.md (non-archive) for unverified goals
  - memory/synthesis/*.md for "open items" / "unresolved" sections  
  - TODO.md for (blocked:) markers
  - memory/ops/blockers.md for NEEDS-HUMAN entries

Outputs new items found (not already in open-items.md).
"""
import os, re, sys
from datetime import date

OPEN_ITEMS_FILE = "memory/scribe/open-items.md"

def load_existing_ids():
    """Load existing item IDs from open-items.md."""
    ids = set()
    if os.path.exists(OPEN_ITEMS_FILE):
        with open(OPEN_ITEMS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                m = re.match(r'\| (OI-\d{3}) \|', line)
                if m:
                    ids.add(m.group(1))
    return ids

def scan_goals():
    """Find unverified goals in current (non-archive) goal files."""
    items = []
    goals_dir = "memory/goals"
    if not os.path.isdir(goals_dir):
        return items
    for fname in sorted(os.listdir(goals_dir)):
        if not fname.endswith('.md') or 'archive' in fname:
            continue
        fpath = os.path.join(goals_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        for m in re.finditer(r'^(\d+)\.\s+\*\*(.+?)\*\*.*$', content, re.MULTILINE):
            goal_text = m.group(0)
            if '(verified:' not in goal_text and 'MOVED' not in goal_text:
                agent = fname.replace('.md', '')
                items.append({
                    'source': f'memory/goals/{fname}',
                    'question': f"[{agent}#{m.group(1)}] {m.group(2)[:80]} - no verified marker",
                    'raised_by': agent,
                    'date': date.today().isoformat(),
                })
    return items

def scan_blockers():
    """Find NEEDS-HUMAN entries in blockers file."""
    items = []
    path = "memory/ops/blockers.md"
    if not os.path.exists(path):
        return items
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    for m in re.finditer(r'(?i)NEEDS-HUMAN.*?(?=\n#|\Z)', content, re.DOTALL):
        text = m.group(0).strip()[:200]
        items.append({
            'source': 'memory/ops/blockers.md',
            'question': f"NEEDS-HUMAN: {text[:150]}",
            'raised_by': "Mechanic",
            'date': date.today().isoformat(),
        })
    return items

def scan_todo_blocked():
    """Find (blocked:) markers in TODO.md."""
    items = []
    if not os.path.exists("TODO.md"):
        return items
    with open("TODO.md", 'r', encoding='utf-8') as f:
        content = f.read()
    for m in re.finditer(r'\(blocked:\s*(.+?)\)', content):
        items.append({
            'source': 'TODO.md',
            'question': f"Blocked: {m.group(1)[:150]}",
            'raised_by': "unknown",
            'date': date.today().isoformat(),
        })
    return items

def main():
    existing_ids = load_existing_ids()
    all_new = []
    
    for scanner in [scan_goals, scan_blockers, scan_todo_blocked]:
        found = scanner()
        # Filter out items whose text matches an existing entry (fuzzy)
        for item in found:
            key = item['question'][:60]
            if key not in str(existing_ids):  # simple check
                all_new.append(item)
    
    if '--report' in sys.argv:
        print(f"Open Items Scan - {date.today().isoformat()}")
        print(f"Existing tracked: {len(existing_ids)} items")
        print(f"New untracked: {len(all_new)} items")
        for i, item in enumerate(all_new[:20], 1):
            print(f"  {i}. [{item['source']}] {item['question']}")
        if len(all_new) > 20:
            print(f"  ... and {len(all_new)-20} more")
    else:
        # JSON output for programmatic use
        import json
        print(json.dumps(all_new, indent=2))

if __name__ == '__main__':
    main()
