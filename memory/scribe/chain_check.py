#!/usr/bin/env python3
"""Supersession Chain Validator for memory/synthesis/.

Checks:
  1. Every 'supersedes X' / 'superseded by Y' reference resolves to an existing file.
  2. No circular references in the supersession DAG.
  3. Dates are monotonic along each chain (later doc supersedes earlier).

Usage: python memory/scribe/chain_check.py
Exit 0 = all checks pass; exit 1 = violations found.
"""
import os, re, sys
from pathlib import Path
from collections import defaultdict

SYNTH_DIR = Path(__file__).resolve().parent.parent / "synthesis"

# Patterns to extract supersession links from file content
RE_SUPERSEDES = re.compile(r'supersedes\s+([\w./-]+\.md)', re.IGNORECASE)
RE_SUPERSEDED_BY = re.compile(r'superseded\s+by\s+([\w./-]+\.md)', re.IGNORECASE)
RE_DATE_PREFIX = re.compile(r'^(\d{4}-\d{2}-\d{2})')

def extract_date(filename: str) -> str | None:
    m = RE_DATE_PREFIX.match(filename)
    return m.group(1) if m else None

def normalize_ref(ref: str, current_dir: Path) -> Path:
    """Resolve a reference like '2026-11-12-upgrade-round.md' or 'memory/synthesis/...'."""
    ref = ref.strip()
    # Try as relative to synthesis dir
    p = SYNTH_DIR / ref
    if p.exists():
        return p
    # Try stripping leading 'memory/synthesis/'
    if ref.startswith('memory/synthesis/'):
        p2 = Path(ref)
        if p2.exists():
            return p2
    return None

def main():
    if not SYNTH_DIR.is_dir():
        print(f"ERROR: {SYNTH_DIR} not found")
        sys.exit(1)

    md_files = sorted(SYNTH_DIR.glob("*.md"))
    print(f"Scanning {len(md_files)} files in {SYNTH_DIR}")

    # Build edges: edge (A -> B) means A supersedes B
    edges = []  # (superseder, superseded)
    unresolved = []
    no_supersession = set()

    for f in md_files:
        text = f.read_text(encoding='utf-8', errors='replace')
        if 'no supersession' in text.lower():
            no_supersession.add(f.name)

        for m in RE_SUPERSEDES.finditer(text):
            ref = m.group(1)
            target = normalize_ref(ref, SYNTH_DIR)
            if target:
                edges.append((f.name, target.name))
            else:
                unresolved.append((f.name, ref, 'supersedes'))

        for m in RE_SUPERSEDED_BY.finditer(text):
            ref = m.group(1)
            target = normalize_ref(ref, SYNTH_DIR)
            if target:
                edges.append((target.name, f.name))  # target supersedes this file
            else:
                unresolved.append((f.name, ref, 'superseded by'))

    print(f"\nEdges found: {len(edges)}")
    for s, t in sorted(set(edges)):
        print(f"  {s} -> supersedes -> {t}")

    # Check 1: Unresolved references
    if unresolved:
        print(f"\n[FAIL] Unresolved references ({len(unresolved)}):")
        for src, ref, kind in unresolved:
            print(f"  {src}: '{kind}' -> {ref} (file not found)")
    else:
        print("\n[PASS] All supersession references resolve to existing files.")

    # Check 2: Circular references (DFS cycle detection)
    graph = defaultdict(list)
    for s, t in set(edges):
        graph[s].append(t)  # s supersedes t, so edge s->t means "s is newer than t"

    def find_cycle():
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {f.name: WHITE for f in md_files}
        parent = {}
        cycle = []

        def dfs(node):
            color[node] = GRAY
            for nei in graph.get(node, []):
                if color.get(nei, BLACK) == GRAY:
                    # Found cycle
                    cyc = [nei, node]
                    cur = node
                    while cur != nei:
                        cur = parent.get(cur)
                        if cur is None or cur == nei:
                            break
                        cyc.append(cur)
                    return list(reversed(cyc))
                if color.get(nei, BLACK) == WHITE:
                    parent[nei] = node
                    result = dfs(nei)
                    if result:
                        return result
            color[node] = BLACK
            return None

        for f in md_files:
            if color[f.name] == WHITE:
                result = dfs(f.name)
                if result:
                    return result
        return None

    cycle = find_cycle()
    if cycle:
        print(f"\n[FAIL] Circular reference detected: {' -> '.join(cycle)}")
    else:
        print("[PASS] No circular references.")

    # Check 3: Date monotonicity along chains
    date_violations = []
    for s, t in set(edges):
        ds = extract_date(s)
        dt = extract_date(t)
        if ds and dt:
            if ds < dt:
                date_violations.append((s, t, f"superseder {s} (date {ds}) is OLDER than superseded {t} (date {dt})"))

    if date_violations:
        print(f"\n[FAIL] Date monotonicity violations ({len(date_violations)}):")
        for s, t, msg in date_violations:
            print(f"  {msg}")
    else:
        print("[PASS] Dates are monotonic along all chains (superseder is always newer).")

    # Summary
    total_issues = len(unresolved) + (1 if cycle else 0) + len(date_violations)
    print(f"\n{'='*50}")
    print(f"RESULT: {'PASS' if total_issues == 0 else f'FAIL ({total_issues} issues)'}")
    print(f"  Files scanned: {len(md_files)}")
    print(f"  Edges: {len(set(edges))}")
    print(f"  No-supersession markers: {len(no_supersession)}")
    sys.exit(0 if total_issues == 0 else 1)

if __name__ == '__main__':
    main()
