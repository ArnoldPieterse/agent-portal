#!/usr/bin/env python3
"""XRef Integrity Monitor - Goal 5 (Archivist, cycle-7)
Rules: no dangling edges, no self-references, max pointer-chain depth <= 3.
Run after every mirror cycle. Exit 0 = clean, 1 = violations found.
"""
import re, sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

MEMORY_ROOT = Path("memory").resolve()
REPO_ROOT = MEMORY_ROOT.parent
MAX_DEPTH = 3  # A->B->C = depth 3 (OK); A->B->C->D = depth 4 (VIOLATION)

def all_md_files():
    return sorted(MEMORY_ROOT.rglob("*.md"))

def rel_to_root(fp):
    try:
        return str(fp.relative_to(REPO_ROOT)).replace('\\', '/')
    except ValueError:
        return str(fp).replace('\\', '/')

def extract_refs(filepath):
    text = filepath.read_text(errors='replace')
    refs = set()
    for m in re.finditer(r'`([^`\n]+?\.(?:md|py|json|html|css|js))`', text):
        refs.add(m.group(1).strip())
    for m in re.finditer(r'->\s*([A-Za-z0-9_./\-]+\.(?:md|py|json|html))', text):
        refs.add(m.group(1).strip())
    for m in re.finditer(r'\(pointer:\s*([A-Za-z0-9_./\-]+)\)', text):
        refs.add(m.group(1).strip())
    return refs

def normalize_ref(ref, source_file):
    ref = ref.strip()
    if ref.startswith('./'):
        ref = ref[2:]
    if ref.startswith(('memory/', 'ui/', 'agents.json', 'TODO.md', 'MEMORY.md')):
        return ref
    candidate = (source_file.parent / ref).resolve()
    try:
        return str(candidate.relative_to(REPO_ROOT)).replace('\\', '/')
    except ValueError:
        return ref

def build_graph():
    files = all_md_files()
    file_set = {rel_to_root(f) for f in files}
    edges = defaultdict(set)
    self_refs, dangling = [], []
    for f in files:
        src = rel_to_root(f)
        for ref in extract_refs(f):
            norm = normalize_ref(ref, f)
            if norm == src:
                self_refs.append(src)
                continue
            if norm.endswith('.md') and norm not in file_set:
                dangling.append((src, norm))
            edges[src].add(norm)
    return edges, self_refs, dangling, file_set

def find_deep_chains(edges, max_depth=MAX_DEPTH):
    violations = []
    def dfs(node, path, visited):
        if len(path) > max_depth:
            if len(violations) < 50:
                violations.append(list(path))
            return
        for nb in sorted(edges.get(node, [])):
            if nb not in visited:
                visited.add(nb)
                path.append(nb)
                dfs(nb, path, visited)
                path.pop()
                visited.discard(nb)
    all_nodes = set(edges.keys())
    for ts in edges.values():
        all_nodes.update(ts)
    for start in sorted(all_nodes)[:150]:
        dfs(start, [start], {start})
    return violations

def suggest_fix(vtype, detail):
    if vtype == 'dangling':
        src, target = detail
        return f"Remove or correct ref to '{target}' in {src}"
    elif vtype == 'self-ref':
        return f"Remove self-reference in {detail}"
    else:
        chain = detail
        return f"Simplify: add direct pointer {chain[0]} -> {chain[-1]}, remove intermediates"

def main():
    print(f"=== XRef Integrity Monitor ===")
    print(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Max chain depth: {MAX_DEPTH}\n")

    edges, self_refs, dangling, file_set = build_graph()
    total_edges = sum(len(v) for v in edges.values())
    print(f"Files scanned: {len(file_set)}")
    print(f"Edges found:   {total_edges}\n")

    print(f"[1] Dangling edges: {len(dangling)}")
    for s, t in dangling[:15]:
        print(f"    {s} -> {t}")
    if len(dangling) > 15:
        print(f"    ... +{len(dangling)-15} more")
    print()

    print(f"[2] Self-references: {len(self_refs)}")
    for sr in self_refs[:10]:
        print(f"    {sr}")
    print()

    deep = find_deep_chains(edges)
    print(f"[3] Chains deeper than {MAX_DEPTH}: {len(deep)}")
    for c in deep[:10]:
        print(f"    {' -> '.join(c)} (depth {len(c)})")
    if len(deep) > 10:
        print(f"    ... +{len(deep)-10} more")
    print()

    total_v = len(dangling) + len(self_refs) + len(deep)
    status = "PASS" if total_v == 0 else "FAIL"
    print(f"=== RESULT: {status} ({total_v} violations) ===\n")

    # Write report
    rpt_dir = MEMORY_ROOT / "archivist"
    rpt_dir.mkdir(parents=True, exist_ok=True)
    rp = rpt_dir / f"xref-monitor-report-{datetime.now().strftime('%Y-%m-%d')}.md"
    lines = [
        "# XRef Integrity Monitor Report",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "", "## Summary",
        f"- Files scanned: {len(file_set)}",
        f"- Edges found: {total_edges}",
        f"- Dangling edges: {len(dangling)}",
        f"- Self-references: {len(self_refs)}",
        f"- Deep chains (>depth {MAX_DEPTH}): {len(deep)}",
        f"- **Status: {status}**", "",
    ]
    if dangling:
        lines.append("## Dangling Edges")
        for s, t in dangling[:50]:
            lines.append(f"- `{s}` -> `{t}` — {suggest_fix('dangling', (s, t))}")
        lines.append("")
    if self_refs:
        lines.append("## Self-References")
        for sr in self_refs[:20]:
            lines.append(f"- `{sr}` — {suggest_fix('self-ref', sr)}")
        lines.append("")
    if deep:
        lines.append("## Deep Chains")
        for c in deep[:20]:
            lines.append(f"- `{' -> '.join(c)}` (depth {len(c)}) — {suggest_fix('deep-chain', c)}")
        lines.append("")
    rp.write_text('\n'.join(lines))
    print(f"Report: {rel_to_root(rp)}")
    return 0 if total_v == 0 else 1

if __name__ == '__main__':
    sys.exit(main())