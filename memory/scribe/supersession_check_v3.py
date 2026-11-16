#!/usr/bin/env python3
"""memory/scribe/supersession_check_v3.py (cycle-2 goal 5, policy owner: Scribe).
Validates against the canonical pointer spec (memory/scribe/supersession-pointer-spec.md):
  - Canonical form: SUPERSEDED BY: <relative/path.ext> in first 10 lines
  - Resolution: target must exist on disk
  - Cycle detection via DFS
Exit 0 = PASS, 1 = FAIL.
"""
import os, re, sys, json, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")

# Canonical: exact keyword + path with extension in first 10 lines
CANONICAL_RE = re.compile(r"^SUPERSEDED BY:\s+([A-Za-z0-9_./\\-]+\.(?:md|py|json|html))\s*$", re.MULTILINE)
# Legacy/prose: any 'superseded by' or 'replaced by' with path-like target
LEGACY_RE = re.compile(r"(?<![-A-Za-z0-9])(?:supersedes?|replaced by)\s*[:\-]?\s*([A-Za-z0-9_./\\-]+)", re.IGNORECASE)

def norm(x):
    x = x.replace("\\", "/")
    while x.startswith("./"): x = x[2:]
    return x

def is_path_like(raw):
    if re.search(r"\.(md|py|json|html)$", raw, re.I): return True
    if raw.startswith(("memory/", "ui/", "agents.", "TODO", "MEMORY")): return True
    return False

# Collect all .md files under memory/
files = set()
for r, d, fs in os.walk(MEM):
    d[:] = [x for x in d if not x.startswith(".")]
    for f in fs:
        if f.endswith(".md"):
            files.add(norm(os.path.relpath(os.path.join(r, f), ROOT)))

bybase = {}
for f in files:
    b2 = f.rsplit("/", 1)[-1]
    bybase.setdefault(b2, f)

canonical_edges = []  # (source_file, target_path) - compliant
legacy_edges = []     # (source_file, raw_target) - non-compliant
header_violations = []  # canonical keyword but NOT in first 10 lines

for rel in sorted(files):
    p = os.path.join(ROOT, *rel.split("/"))
    try:
        txt = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    lines = txt.splitlines()
    header_block = "\n".join(lines[:10])

    # Check canonical in header block
    for m in CANONICAL_RE.finditer(header_block):
        canonical_edges.append((rel, norm(m.group(1))))

    # Check if canonical keyword appears outside header (violation)
    body = "\n".join(lines[10:])
    if CANONICAL_RE.search(body):
        header_violations.append(rel)

    # Check legacy/prose mentions
    for m in LEGACY_RE.finditer(txt):
        raw = m.group(1)
        if is_path_like(raw) and not any(c[0] == rel and c[1] == norm(raw) for c in canonical_edges):
            legacy_edges.append((rel, norm(raw)))

# Resolve edges
def resolve(target):
    if target in files: return target
    if os.path.exists(os.path.join(ROOT, *target.split("/"))): return target
    rb = bybase.get(target.rsplit("/", 1)[-1])
    return rb

canonical_resolved = []
for a, b in canonical_edges:
    r = resolve(b)
    canonical_resolved.append((a, b, r))

dangling_canonical = [(a, b) for a, b, r in canonical_resolved if r is None]
legacy_resolved = []
for a, b in legacy_edges:
    r = resolve(b)
    legacy_resolved.append((a, b, r))
dangling_legacy = [(a, b) for a, b, r in legacy_resolved if r is None]

# Cycle detection on canonical edges only
adj = collections.defaultdict(set)
for a, b, r in canonical_resolved:
    if r: adj[a].add(r)
state, bad = {}, []
def dfs(n):
    state[n] = 1
    for m in adj.get(n, ()):
        if state.get(m) == 1: bad.append((n, m))
        elif not state.get(m): dfs(m)
    state[n] = 2
for n in list(adj):
    if not state.get(n): dfs(n)

total_supersession_mentions = len(canonical_edges) + len(legacy_edges)
compliance_rate = (len(canonical_edges) / total_supersession_mentions * 100) if total_supersession_mentions else 100.0

report = {
    "run_at": datetime.datetime.now().isoformat(),
    "script": "memory/scribe/supersession_check_v3.py",
    "spec": "memory/scribe/supersession-pointer-spec.md",
    "policy_owner": "Scribe (goal 5)",
    "total_md_files_scanned": len(files),
    "canonical_pointers": len(canonical_edges),
    "legacy_prose_mentions": len(legacy_edges),
    "header_violations": header_violations,
    "compliance_rate_pct": round(compliance_rate, 1),
    "canonical_dangling": [{"source": a, "target": b} for a, b in dangling_canonical],
    "legacy_dangling_count": len(dangling_legacy),
    "cycles_detected": len(bad),
    "cycle_detail": [{"a": x, "b": y} for x, y in bad],
    "verdict": "PASS" if (not dangling_canonical and not bad) else "FAIL",
    "note": "PASS = zero dangling canonical pointers AND zero cycles. Legacy prose is tracked but not a FAIL condition until migration completes."
}

out_path = os.path.join(ROOT, "memory/scribe/supersession-report-v3.json")
with open(out_path, "w") as f:
    json.dump(report, f, indent=2)

print(f"supersession_check v3: {len(canonical_edges)} canonical, {len(legacy_edges)} legacy, compliance={compliance_rate:.1f}%")
print(f"  dangling canonical: {len(dangling_canonical)}, cycles: {len(bad)}, header violations: {len(header_violations)}")
print(f"Verdict: {report['verdict']}")
sys.exit(0 if report["verdict"] == "PASS" else 1)