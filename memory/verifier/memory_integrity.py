#!/usr/bin/env python3
"""Memory Tree Integrity Check - Verifier Goal #9.

Checks:
  1. No orphaned files (not referenced by any INDEX.md)
  2. No broken pointer lines (pointer: / Evidence: -> target exists)
  3. No circular references between INDEX files
  4. File sizes within budgets (INDEX < 1600 chars)

Usage: python memory/verifier/memory_integrity.py [--json]
"""
import os, re, sys, json
from pathlib import Path
from collections import defaultdict

ROOT = Path("memory")
REPORT = "memory/ops/memory-integrity-2026-11-20.md"
INDEX_BUDGET = 1600  # chars

def find_index_files():
    """Find all INDEX.md files under memory/."""
    return sorted(ROOT.rglob("INDEX.md"))

def find_all_md_files():
    """Find all .md files under memory/ (excluding INDEX.md)."""
    return sorted(p for p in ROOT.rglob("*.md") if p.name != "INDEX.md")

def extract_pointers(text):
    """Extract pointer targets from text. Returns list of relative paths."""
    targets = []
    # Pattern: -> path  or  pointer: path  or  Evidence: path
    for m in re.finditer(r'(?:->|pointer:|Evidence:|evidence:)\s*([A-Za-z0-9_./\\-]+\.md)', text):
        targets.append(m.group(1).replace("\\", "/"))
    # Also capture non-.md file references in pointer lines
    for m in re.finditer(r'(?:pointer:|->)\s*([A-Za-z0-9_./\\-]+\.py)', text):
        targets.append(m.group(1).replace("\\", "/"))
    return targets

def resolve_target(target):
    """Resolve a relative target path to absolute under memory/ or project root."""
    t = Path(target)
    # Try relative to memory/
    candidates = [ROOT / t, Path(".") / t]
    for c in candidates:
        if c.exists():
            return c
    return None

def check_orphans(index_files, all_md):
    """Find .md files not referenced by any INDEX.md."""
    # Build set of all referenced paths
    referenced = set()
    for idx in index_files:
        try:
            text = idx.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        targets = extract_pointers(text)
        for t in targets:
            resolved = resolve_target(t)
            if resolved:
                referenced.add(resolved.resolve())
    # Also: files in the same directory as an INDEX.md are implicitly indexed
    for idx in index_files:
        for sibling in idx.parent.iterdir():
            if sibling.is_file() and sibling.suffix == ".md":
                referenced.add(sibling.resolve())
    orphans = []
    for f in all_md:
        try:
            fr = f.resolve()
        except OSError:
            continue
        if fr not in referenced:
            # Skip files in _archived dirs, TODO.md, MEMORY.md (root-level special)
            parts = f.parts
            if any(p.startswith("_archived") or p == "archive" for p in parts):
                continue
            if f.name in ("TODO.md", "MEMORY.md"):
                continue
            orphans.append(str(f))
    return orphans

def check_broken_pointers(index_files, all_md):
    """Find pointer lines whose targets don't exist."""
    broken = []
    all_files_resolved = set()
    for f in list(all_md) + list(index_files):
        try:
            all_files_resolved.add(f.resolve())
        except OSError:
            pass
    # Also include .py files
    for py in ROOT.rglob("*.py"):
        try:
            all_files_resolved.add(py.resolve())
        except OSError:
            pass

    check_files = list(index_files) + list(all_md)
    for f in check_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        targets = extract_pointers(text)
        for t in targets:
            resolved = resolve_target(t)
            if resolved is None:
                broken.append({"file": str(f), "target": t})
    return broken

def check_circular(index_files):
    """Detect circular references between INDEX.md files."""
    graph = defaultdict(set)
    index_set = {p.resolve() for p in index_files}
    for idx in index_files:
        try:
            text = idx.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        targets = extract_pointers(text)
        for t in targets:
            resolved = resolve_target(t)
            if resolved and resolved.resolve() in index_set:
                graph[idx.resolve()].add(resolved.resolve())
    # DFS for cycles
    visited = set()
    stack = set()
    cycles = []
    def dfs(node, path):
        visited.add(node)
        stack.add(node)
        path.append(str(node))
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor, path)
            elif neighbor in stack:
                cycle_start = path.index(str(neighbor))
                cycles.append(path[cycle_start:] + [str(neighbor)])
        path.pop()
        stack.discard(node)
    for node in list(graph.keys()):
        if node not in visited:
            dfs(node, [])
    return cycles

def check_sizes(index_files):
    """Check INDEX.md files are within budget."""
    oversized = []
    for idx in index_files:
        try:
            size = len(idx.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if size > INDEX_BUDGET:
            oversized.append({"file": str(idx), "size": size, "budget": INDEX_BUDGET})
    return oversized

def main():
    index_files = find_index_files()
    all_md = find_all_md_files()

    print(f"Scanning {ROOT}/ : {len(index_files)} INDEX.md, {len(all_md)} content .md files")

    orphans = check_orphans(index_files, all_md)
    broken = check_broken_pointers(index_files, all_md)
    cycles = check_circular(index_files)
    oversized = check_sizes(index_files)

    # Summary
    total_issues = len(orphans) + len(broken) + len(cycles) + len(oversized)
    status = "PASS" if total_issues == 0 else f"FAIL ({total_issues} issues)"
    print(f"\n=== Memory Tree Integrity: {status} ===")
    print(f"  Orphaned files:   {len(orphans)}")
    print(f"  Broken pointers:  {len(broken)}")
    print(f"  Circular refs:    {len(cycles)}")
    print(f"  Oversized INDEX:  {len(oversized)} (budget {INDEX_BUDGET} chars)")

    if orphans:
        print(f"\n  Orphaned files (not in any INDEX.md):")
        for o in orphans[:20]:
            print(f"    - {o}")
        if len(orphans) > 20:
            print(f"    ... and {len(orphans)-20} more")

    if broken:
        print(f"\n  Broken pointer targets:")
        for b in broken[:20]:
            print(f"    - {b['file']} -> {b['target']}")
        if len(broken) > 20:
            print(f"    ... and {len(broken)-20} more")

    if cycles:
        print(f"\n  Circular reference chains:")
        for c in cycles[:5]:
            print(f"    - {' -> '.join(c)}")

    if oversized:
        print(f"\n  Oversized INDEX files:")
        for o in oversized:
            print(f"    - {o['file']}: {o['size']} chars (budget {o['budget']})")

    # Write report
    lines = ["# Memory Tree Integrity Report",
             f"Run: 2026-11-20 | Status: **{status}**",
             "",
             f"| Check | Result | Count |", "|---|---|---|",
             f"| Orphaned files | {'PASS' if not orphans else 'FAIL'} | {len(orphans)} |",
             f"| Broken pointers | {'PASS' if not broken else 'FAIL'} | {len(broken)} |",
             f"| Circular refs | {'PASS' if not cycles else 'FAIL'} | {len(cycles)} |",
             f"| INDEX size budget | {'PASS' if not oversized else 'FAIL'} | {len(oversized)} |",
             ""]
    if orphans:
        lines.append("## Orphaned Files")
        for o in orphans[:50]:
            lines.append(f"- `{o}`")
        if len(orphans) > 50:
            lines.append(f"- ... and {len(orphans)-50} more")
        lines.append("")
    if broken:
        lines.append("## Broken Pointers")
        for b in broken[:50]:
            lines.append(f"- `{b['file']}` -> `{b['target']}`")
        if len(broken) > 50:
            lines.append(f"- ... and {len(broken)-50} more")
        lines.append("")
    if cycles:
        lines.append("## Circular References")
        for c in cycles[:10]:
            lines.append(f"- {' -> '.join(c)}")
        lines.append("")
    if oversized:
        lines.append("## Oversized INDEX Files")
        for o in oversized:
            lines.append(f"- `{o['file']}`: {o['size']} chars (budget {o['budget']})")
        lines.append("")

    Path(REPORT).write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport written to {REPORT}")

    # JSON output if requested
    if "--json" in sys.argv:
        data = {
            "status": status,
            "orphans": orphans,
            "broken_pointers": broken,
            "circular_refs": cycles,
            "oversized_index": oversized,
            "totals": {"index_files": len(index_files), "content_md": len(all_md), "issues": total_issues}
        }
        print(json.dumps(data, indent=2))

    return 0 if total_issues == 0 else 1

if __name__ == "__main__":
    sys.exit(main())