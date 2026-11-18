#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate_decisions.py - Extract structured decision entries from memory/synthesis/ files.

Usage:
    python memory/scribe/migrate_decisions.py              # scan all synthesis files, report candidates
    python memory/scribe/migrate_decisions.py --apply      # show candidates grouped by file
    python memory/scribe/migrate_decisions.py --validate   # check existing decision_log.md for completeness

Each decision entry requires 6 fields: date, decision, context, alternatives_considered, rationale, owner.
"""

import os
import re
import sys
from datetime import datetime

SYNTHESIS_DIR = "memory/synthesis"
DECISION_LOG = "memory/scribe/decision_log.md"

# Patterns that indicate a decision was made in a synthesis file
DECISION_PATTERNS = [
    r"\*\*?D[0-9]+\*\*?",           # D1, D2, ... (bold or plain)
    r"RULING:\s*",                     # Orchestrator rulings
    r"## Decided",                      # "Decided" section header
    r"\*\*decision\*\*:",           # explicit decision field
    r"FIX [0-9]+",                      # numbered fixes
    r"DECISION NEEDED",                 # flagged decisions
]

def scan_synthesis_files():
    """Scan all synthesis .md files for decision-like content. Returns list of candidates."""
    candidates = []
    if not os.path.isdir(SYNTHESIS_DIR):
        print(f"ERROR: {SYNTHESIS_DIR} not found")
        return candidates
    
    for fname in sorted(os.listdir(SYNTHESIS_DIR)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(SYNTHESIS_DIR, fname)
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        # Extract date from filename (YYYY-MM-DD prefix)
        date_match = re.match(r"(\d{4}-\d{2}-\d{2})", fname)
        date = date_match.group(1) if date_match else "unknown"
        
        # Find decision-like lines
        for i, line in enumerate(content.split("\n")):
            for pattern in DECISION_PATTERNS:
                if re.search(pattern, line):
                    candidates.append({
                        "file": fpath,
                        "date": date,
                        "line_num": i + 1,
                        "text": line.strip()[:200],
                        "pattern_matched": pattern,
                    })
                    break  # one match per line is enough
    
    return candidates

def validate_decision_log():
    """Check that decision_log.md has >=10 entries, each with all 6 fields."""
    if not os.path.exists(DECISION_LOG):
        print(f"FAIL: {DECISION_LOG} does not exist")
        return False
    
    with open(DECISION_LOG, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    # Count decision entries (## D-XXX headers)
    entries = re.findall(r"^## (D-\d+)", content, re.MULTILINE)
    count = len(entries)
    
    print(f"Entries found: {count}")
    
    if count < 10:
        print(f"FAIL: need >=10 decisions, found {count}")
        return False
    
    # Check each entry has all 6 required fields
    required_fields = ["decision", "context", "alternatives_considered", "rationale", "owner"]
    # Split by entry headers
    blocks = re.split(r"^## D-\d+", content, flags=re.MULTILINE)[1:]  # skip preamble
    
    all_valid = True
    for i, block in enumerate(blocks):
        missing = []
        for field in required_fields:
            if f"**{field}**" not in block and f"**{field.replace('_',' ')}**" not in block:
                missing.append(field)
        if missing:
            print(f"  Entry {i+1}: MISSING fields: {missing}")
            all_valid = False
    
    if all_valid:
        print(f"PASS: {count} entries, all have required fields")
    else:
        print(f"FAIL: some entries missing fields")
    
    return all_valid

def apply_new_decisions(candidates):
    """Report candidates for manual review (auto-appending requires human judgment on 6 fields)."""
    print(f"\n{'='*60}")
    print(f"CANDIDATES FOUND: {len(candidates)}")
    print(f"{'='*60}")
    print("\nNOTE: Auto-extraction identifies decision-LIKELY lines.")
    print("Full 6-field entries require manual curation (context, alternatives, rationale).")
    print("Use these as a starting point for adding to decision_log.md.\n")
    
    # Group by file
    by_file = {}
    for c in candidates:
        by_file.setdefault(c["file"], []).append(c)
    
    for fpath, items in sorted(by_file.items()):
        print(f"  {fpath} ({len(items)} candidates):")
        for item in items[:5]:  # show max 5 per file
            print(f"    L{item['line_num']}: {item['text'][:100]}")
        if len(items) > 5:
            print(f"    ... and {len(items)-5} more")
        print()

def main():
    if "--validate" in sys.argv:
        ok = validate_decision_log()
        sys.exit(0 if ok else 1)
    
    candidates = scan_synthesis_files()
    
    if "--apply" in sys.argv:
        apply_new_decisions(candidates)
    else:
        # Default: just report count + validation
        print(f"Scanned {SYNTHESIS_DIR}/ for decision patterns...")
        print(f"Candidates found: {len(candidates)}")
        print()
        ok = validate_decision_log()
        sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
