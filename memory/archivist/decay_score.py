#!/usr/bin/env python3
"""archivist/decay_score.py (cycle-2 goal 7).
Scores every memory leaf: recency x reference-density x index-linkage. Composite below
threshold -> flagged for review/archival in decay-report.md. Exit 0 always."""
import os, re, math, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
TODAY = datetime.date.today()

# index-linkage: which files are referenced by some INDEX.md
indexed = set()
for r, d, fs in os.walk(MEM):
    if "INDEX.md" in fs:
        for line in open(os.path.join(r, "INDEX.md"), encoding="utf-8", errors="replace"):
            m = re.search(r"->\s*([A-Za-z0-9_./\\-]+\.\w+)", line)
            if m: indexed.add(m.group(1).replace("\\", "/"))

# reference density: how many other files point at this one
refs = {}
allfiles = {}
for r, d, fs in os.walk(MEM):
    d[:] = [x for x in d if not x.startswith(".")]
    for f in fs:
        p = os.path.join(r, f)
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        allfiles[rel] = p
        try: txt = open(p, encoding="utf-8", errors="replace").read()
        except Exception: continue
        for m in re.finditer(r"->\s*([A-Za-z0-9_./\\-]+\.\w+)|\]\(([A-Za-z0-9_./\\-]+\.\w+)\)", txt):
            t = (m.group(1) or m.group(2)).replace("\\", "/")
            refs[t] = refs.get(t, 0) + 1

rows = []
for rel, p in allfiles.items():
    if os.path.basename(rel) == "INDEX.md": continue
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).date()
    age = (TODAY - mt).days
    recency = max(0.0, 1.0 - age / 90.0)                    # 0 at 90d
    density = math.log1p(refs.get(rel, 0)) / 3.0            # saturates ~3 refs
    linkage = 1.0 if rel in indexed else 0.25
    score = round(0.5 * recency + 0.3 * min(density, 1.0) + 0.2 * linkage, 3)
    rows.append((rel, age, refs.get(rel, 0), "Y" if rel in indexed else "n", score))

low = [x for x in rows if x[4] < 0.35]
out = os.path.join(MEM, "archivist", "decay-report.md")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("# Decay report %s\n\nLeaves: %d | flagged (<0.35): %d\n\n" % (TODAY.isoformat(), len(rows), len(low)))
    fh.write("| leaf | age_d | inrefs | indexed | score |\n|---|---|---|---|---|\n")
    for rel, age, ir, ix, sc in sorted(rows, key=lambda x: x[4]):
        mark = " **FLAG**" if sc < 0.35 else ""
        fh.write("| %s | %d | %d | %s | %.3f%s |\n" % (rel, age, ir, ix, sc, mark))
print("decay_score: %d leaves, %d flagged -> %s" % (len(rows), len(low), os.path.relpath(out, ROOT)))
for rel, age, ir, ix, sc in sorted(rows, key=lambda x: x[4])[:8]:
    print("  %.3f age=%dd refs=%d idx=%s %s" % (sc, age, ir, ix, rel))
