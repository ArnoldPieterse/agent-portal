#!/usr/bin/env python3
"""archivist/memory_health.py (cycle-2 goal 2).
Per-leaf freshness against declared TTL classes; writes memory/archivist/freshness-report.md.
TTLs: ops runbooks <=14d, architecture/portal <=30d, goals = cycle length (7d), other 60d.
Exit 0 = all fresh, 2 = stale leaves present (soft, informational)."""
import os, re, time, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")
TODAY = datetime.date.today()

def ttl_for(rel):
    if "/ops/" in rel: return 14
    if "/portal/" in rel or "architecture" in rel: return 30
    if "/goals/" in rel: return 7
    return 60

def leaf_date(rel, mtime):
    # prefer a date in the filename (YYYY-MM-DD), else mtime
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", os.path.basename(rel))
    if m: return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return datetime.datetime.fromtimestamp(mtime).date()

def main():
    rows = []
    for r, d, fs in os.walk(MEM):
        d[:] = [x for x in d if not x.startswith(".")]
        for f in fs:
            p = os.path.join(r, f)
            rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
            if f == "INDEX.md": continue
            ld = leaf_date(rel, os.path.getmtime(p))
            age = (TODAY - ld).days
            ttl = ttl_for(rel)
            rows.append((rel, str(ld), age, ttl, "STALE" if age > ttl else "ok"))
    stale = [x for x in rows if x[4] == "STALE"]
    out = os.path.join(MEM, "archivist", "freshness-report.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# Freshness report %s\n\n" % TODAY.isoformat())
        fh.write("Leaves: %d | stale (past TTL): %d\n\n| leaf | dated | age_d | ttl_d | state |\n|---|---|---|---|---|\n"
                 % (len(rows), len(stale)))
        for rel, ld, age, ttl, st in sorted(rows, key=lambda x: -x[2])[:40]:
            fh.write("| %s | %s | %d | %d | %s |\n" % (rel, ld, age, ttl, st))
    print("memory_health: %d leaves, %d stale -> %s" % (len(rows), len(stale), os.path.relpath(out, ROOT)))
    for rel, ld, age, ttl, st in sorted(stale, key=lambda x: -x[2])[:10]:
        print("  STALE %dd/%dd: %s" % (age, ttl, rel))
    raise SystemExit(2 if stale else 0)

if __name__ == "__main__":
    main()
