#!/usr/bin/env python3
"""durable_check.py — Scribe Goal #6: Durable-copy guarantee enforcement.

Checks that every leaf file under memory/ has a corresponding entry in its
directory's INDEX.md (or a parent INDEX). Exits 1 on violations (CI-friendly).

Usage:
    python durable_check.py [memory_root]   # default: "memory"
"""
import os, re, sys, json
from datetime import date

def find_index_files(memory_root="memory"):
    indexes = []
    for dirpath, _, filenames in os.walk(memory_root):
        if "INDEX.md" in filenames:
            indexes.append(os.path.join(dirpath, "INDEX.md"))
    return indexes

def parse_index_entries(index_path):
    try:
        with open(index_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return set()
    entries = set()
    for m in re.finditer(r'->\s*([\w/\\.\-]+)', content):
        entries.add(m.group(1).replace("\\", "/"))
    for m in re.finditer(r'`([\w/\\.\-]+\.\w+)`', content):
        entries.add(m.group(1).replace("\\", "/"))
    for m in re.finditer(r'\b([\w\-]+\.(?:md|py|json|js|css|html))\b', content):
        entries.add(m.group(1))
    return entries

def collect_leaves(memory_root="memory"):
    leaves = []
    skip_names = {"INDEX.md", "MEMORY.md"}
    for dirpath, _, filenames in os.walk(memory_root):
        for fn in filenames:
            if fn in skip_names:
                continue
            full = os.path.join(dirpath, fn).replace("\\", "/")
            leaves.append(full)
    return leaves

def check_durable(memory_root="memory"):
    indexes = find_index_files(memory_root)
    all_index_entries = set()
    for idx in indexes:
        all_index_entries.update(parse_index_entries(idx))
    leaves = collect_leaves(memory_root)
    violations = []
    for leaf in leaves:
        basename = os.path.basename(leaf)
        rel_from_memory = leaf[len(memory_root)+1:] if leaf.startswith(memory_root + "/") else leaf
        found = any(
            basename == e or rel_from_memory == e or e.endswith("/" + basename)
            for e in all_index_entries
        )
        if not found:
            violations.append(leaf)
    return leaves, violations

def main():
    mem_root = sys.argv[1] if len(sys.argv) > 1 else "memory"
    leaves, violations = check_durable(mem_root)
    result = {
        "checked_at": str(date.today()),
        "total_leaves_checked": len(leaves),
        "violation_count": len(violations),
        "violations_sample": violations[:50],
        "pass": len(violations) == 0
    }
    print(json.dumps(result, indent=2))
    if violations:
        print(f"\nFAIL: {len(violations)} leaf(s) without INDEX entry", file=sys.stderr)
        for v in violations[:10]:
            print(f"  - {v}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nPASS: all leaves have INDEX entries.")
        sys.exit(0)

if __name__ == "__main__":
    main()