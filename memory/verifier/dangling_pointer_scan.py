#!/usr/bin/env python
"""Reusable dangling-pointer scanner (Verifier, 2026-11-20).

Finds `(pointer: <leaf>)` references in memory/goals/*.md whose target leaf is
MISSING or NOT connected to any index. Feeds Archivist goal #2 (Cross-Reference
Integrity Monitor). Exit 0 = clean, 1 = dangling found.

Usage: python memory/verifier/dangling_pointer_scan.py [--active-only]
  --active-only  restrict to live goal files (skip archive/) + flag prose placeholders
"""
import importlib.util, os, sys, glob, re

def _load_ledger():
    d = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(d, "..", "researcher", "goal_ledger.py")
    spec = importlib.util.spec_from_file_location("gl", os.path.normpath(p))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def main():
    gl = _load_ledger()
    root = os.getcwd()
    active_only = "--active-only" in sys.argv
    # treat these as prose placeholders, not real references
    placeholder = re.compile(r"^(relpath|<[^>]+>|\.\.{2,}|%s|⚠.*)$", re.I)
    dangling = []
    total = 0
    files = sorted(glob.glob(os.path.join(root, "memory", "goals", "*.md")))
    if active_only:
        files = [f for f in files if os.sep + "archive" not in f.lower()]
    for f in files:
        try: txt = open(f, encoding="utf-8", errors="replace").read()
        except Exception: continue
        for i, line in enumerate(txt.splitlines(), 1):
            for m in gl.POINTER_PAT.finditer(line):
                leaf = m.group(1).strip(); total += 1
                if placeholder.match(leaf):   # prose example, not a real ref
                    continue
                ok, why = gl.validate_pointer(root, leaf)
                if not ok:
                    dangling.append((os.path.relpath(f, root), i, leaf, why))
    print("pointers scanned: %d" % total)
    print("dangling (real):  %d" % len(dangling))
    for d in dangling:
        print("  [%s] %s:%d -> %s  (%s)" % (d[3].split(":")[0], d[0], d[1], d[2], d[3]))
    return 1 if dangling else 0

if __name__ == "__main__":
    sys.exit(main())
