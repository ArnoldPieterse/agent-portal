#!/usr/bin/env python3
"""Citation Tracking (Archivist Goal #9, cycle-8).

Builds memory/archivist/citation-map.json:
  - For each evidence leaf: which goal files cite it
  - For each goal file: which evidence leaves support it
  - Flags stale citations (evidence mtime > citing file mtime)

Patterns extracted from .md files:
  - (pointer: <relpath>)
  - (verified: ... <relpath> ...)
  - Evidence: <relpath>
  - evidence: <relpath>
  - Source evidence: <relpath>
  - Backtick-wrapped paths that look like memory/ leaves
"""
import re, os, json, glob, datetime, sys

# Patterns for extracting file references
POINTER_RE = re.compile(r'\(pointer:\s*([\w./-]+)\)', re.I)
VERIFIED_RE = re.compile(r'\(verified:\s*[^)]*?([\w][\w./-]*\.md)\s*[^)]*\)', re.I)
EVIDENCE_LINE_RE = re.compile(r'(?:^|\s)(?:Evidence|evidence|Source evidence):\s*(.+)$', re.M)
BACKTICK_PATH_RE = re.compile(r'`((?:memory|TODO)[/\\][\w./-]+\.md)`')
ALL_FILE_RE = re.compile(r'\b(memory/[\w./-]+\.md)\b')

# Only count files under memory/ as evidence leaves (not goals themselves)
GOAL_PREFIXES = ('memory/goals/', 'TODO.md', 'MEMORY.md')

def is_goal_file(path):
    p = path.replace('\\', '/')
    return any(p.startswith(g) for g in GOAL_PREFIXES)

def normalize(p):
    return p.replace('\\', '/').lstrip('./')

def main():
    # Collect all .md files
    all_files = glob.glob('memory/**/*.md', recursive=True)
    all_files += ['TODO.md', 'MEMORY.md'] if os.path.exists('TODO.md') else []
    all_set = set(normalize(f) for f in all_files)

    # mtime map
    mtimes = {}
    for f in all_files:
        try:
            mtimes[normalize(f)] = os.path.getmtime(f)
        except OSError:
            pass

    # citation_map: citing_file -> {cited_file: [line_numbers]}
    raw_citations = {}  # (citing, cited) -> list of line numbers

    for f in all_files:
        rel = normalize(f)
        try:
            lines = open(f, encoding='utf-8', errors='replace').readlines()
        except Exception:
            continue

        for i, line in enumerate(lines, 1):
            refs = set()
            # Pattern 1: (pointer: path)
            for m in POINTER_RE.finditer(line):
                refs.add(normalize(m.group(1)))
            # Pattern 2: (verified: ... path.md ...)
            for m in VERIFIED_RE.finditer(line):
                refs.add(normalize(m.group(1)))
            # Pattern 3: Evidence: path(s)
            for m in EVIDENCE_LINE_RE.finditer(line):
                # Extract all .md paths from the evidence line content
                for pm in re.finditer(r'([\w][\w./-]*\.md)', m.group(1)):
                    refs.add(normalize(pm.group(1)))
            # Pattern 4: backtick-wrapped memory/ paths
            for m in BACKTICK_PATH_RE.finditer(line):
                refs.add(normalize(m.group(1)))
            # Pattern 5: bare memory/*.md references (only if the line has pointer/evidence context)
            if any(kw in line.lower() for kw in ('pointer:', 'evidence:', 'verified:', 'source evidence')):
                for m in ALL_FILE_RE.finditer(line):
                    refs.add(normalize(m.group(1)))

            # Filter: only keep refs that exist and are different from self
            for r in refs:
                if r == rel:
                    continue
                if r not in all_set:
                    continue
                key = (rel, r)
                raw_citations.setdefault(key, []).append(i)

    # Build bidirectional map
    goal_to_evidence = {}   # goal file -> [evidence files]
    evidence_to_goals = {}  # evidence file -> [goal files that cite it]
    all_edges = []

    for (citing, cited), line_nums in sorted(raw_citations.items()):
        edge = {
            "citing": citing,
            "cited": cited,
            "lines": line_nums[:5],  # cap at 5 line refs
            "type": "pointer" if any('pointer' in open(citing, encoding='utf-8', errors='replace').readlines()[ln-1].lower() for ln in line_nums[:1]) else "evidence",
        }
        all_edges.append(edge)

        if is_goal_file(citing):
            goal_to_evidence.setdefault(citing, []).append(cited)
        if not is_goal_file(cited) and is_goal_file(citing):
            evidence_to_goals.setdefault(cited, []).append(citing)

    # Stale detection: cited file modified AFTER citing file
    stale = []
    for (citing, cited), line_nums in raw_citations.items():
        c_mtime = mtimes.get(citing, 0)
        e_mtime = mtimes.get(cited, 0)
        if e_mtime > c_mtime:
            stale.append({
                "citing": citing,
                "cited": cited,
                "citing_mtime": datetime.datetime.fromtimestamp(c_mtime).strftime("%Y-%m-%d %H:%M"),
                "cited_mtime": datetime.datetime.fromtimestamp(e_mtime).strftime("%Y-%m-%d %H:%M"),
            })

    # Deduplicate goal_to_evidence and evidence_to_goals
    for k in goal_to_evidence:
        goal_to_evidence[k] = sorted(set(goal_to_evidence[k]))
    for k in evidence_to_goals:
        evidence_to_goals[k] = sorted(set(evidence_to_goals[k]))

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = {
        "generated": now,
        "total_files_scanned": len(all_files),
        "total_citation_edges": len(all_edges),
        "goal_files_with_citations": len(goal_to_evidence),
        "evidence_files_cited_by_goals": len(evidence_to_goals),
        "stale_citations": stale,
        "stale_count": len(stale),
        "goal_to_evidence": goal_to_evidence,
        "evidence_to_goals": evidence_to_goals,
        "all_edges": all_edges[:200],  # cap for file size
    }

    out_path = 'memory/archivist/citation-map.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    sz = os.path.getsize(out_path)
    print(f"citation-map.json written: {sz/1024:.1f} KB")
    print(f"  files scanned: {len(all_files)}")
    print(f"  citation edges: {len(all_edges)}")
    print(f"  goal files with citations: {len(goal_to_evidence)}")
    print(f"  evidence files cited by goals: {len(evidence_to_goals)}")
    print(f"  stale citations: {len(stale)}")
    if stale:
        for s in stale[:5]:
            print(f"    STALE: {s['citing']} -> {s['cited']} (evidence newer: {s['cited_mtime']})")

if __name__ == "__main__":
    main()
