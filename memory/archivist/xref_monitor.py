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

def _run_on_root(mroot, rroot):
    """Run the pure graph logic against an arbitrary root (used by selftest)."""
    global MEMORY_ROOT, REPO_ROOT
    prev = (MEMORY_ROOT, REPO_ROOT)
    MEMORY_ROOT, REPO_ROOT = mroot, rroot
    try:
        edges, self_refs, dangling, file_set = build_graph()
        deep = find_deep_chains(edges)
        return len(file_set), sum(len(v) for v in edges.values()), dangling, self_refs, deep
    finally:
        MEMORY_ROOT, REPO_ROOT = prev

def _selftest():
    """Controlled acceptance test (Goal 5):
       (a) a DELIBERATELY deep chain A->B->C->D is caught (and is the ONLY violation),
       (b) a CLEAN fixture (depth<=3, no dangling/self-ref) passes with 0 violations.
    Returns 0 pass / 1 fail."""
    import tempfile
    ok = True
    print("=== XRef Monitor SELFTEST ===")

    # --- Fixture A: deliberate deep chain A->B->C->D (depth 4 > MAX_DEPTH) ---
    with tempfile.TemporaryDirectory() as td:
        mem = Path(td) / "memory"; mem.mkdir()
        (mem / "A.md").write_text("start -> B.md\n")
        (mem / "B.md").write_text("mid -> C.md\n")
        (mem / "C.md").write_text("end -> D.md\n")
        (mem / "D.md").write_text("leaf, no outgoing refs.\n")
        nfiles, nedges, dangling, self_refs, deep = _run_on_root(mem, Path(td))
        caught = any(len(c) > MAX_DEPTH for c in deep)
        isolated = (len(dangling) == 0 and len(self_refs) == 0)
        a_pass = caught and isolated
        print(f"[A] deliberate depth-4 chain: files={nfiles} edges={nedges} "
              f"deep_chains={len(deep)} dangling={len(dangling)} selfref={len(self_refs)}")
        for c in deep[:3]:
            print(f"      flagged: {' -> '.join(c)} (depth {len(c)})")
        print(f"[A] expected=caught+isolated  got caught={caught} isolated={isolated}")
        ok = ok and a_pass

    # --- Fixture B: clean, depth<=3 only (E->F->G), no dangling/self-ref ---
    with tempfile.TemporaryDirectory() as td:
        mem = Path(td) / "memory"; mem.mkdir()
        (mem / "E.md").write_text("head -> F.md\n")
        (mem / "F.md").write_text("mid -> G.md\n")
        (mem / "G.md").write_text("tail, no outgoing refs.\n")
        nfiles, nedges, dangling, self_refs, deep = _run_on_root(mem, Path(td))
        total_v = len(dangling) + len(self_refs) + len(deep)
        b_pass = (total_v == 0 and nfiles == 3)
        print(f"[B] clean depth-3 fixture: files={nfiles} violations={total_v}")
        print(f"[B] expected=0 violations  got={total_v}")
        ok = ok and b_pass

    status = "PASS" if ok else "FAIL"
    print(f"=== SELFTEST RESULT: {status} ===")
    return 0 if ok else 1

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return _selftest()
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
