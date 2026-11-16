#!/usr/bin/env python3
"""archivist/snapshot.py (cycle-2 goal 9).
Hashes every memory/ leaf into manifest-YYYYMMDD.json. `--diff` compares against the most
recent earlier manifest and prints added/removed/modified. Exit 0."""
import os, re, sys, json, hashlib, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEM = os.path.join(ROOT, "memory")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""): h.update(c)
    return h.hexdigest()[:16]

def current():
    out = {}
    for r, d, fs in os.walk(MEM):
        d[:] = [x for x in d if not x.startswith(".")]
        for f in fs:
            p = os.path.join(r, f)
            out[os.path.relpath(p, ROOT).replace(os.sep, "/")] = sha(p)
    return out

def main():
    today = datetime.date.today().strftime("%Y%m%d")
    here = os.path.dirname(os.path.abspath(__file__))
    cur = current()
    if "--diff" in sys.argv:
        prevs = sorted(f for f in os.listdir(here) if re.match(r"manifest-\d{8}\.json$", f))
        if not prevs:
            print("snapshot: no earlier manifest to diff"); return
        prev = json.load(open(os.path.join(here, prevs[-1]), encoding="utf-8"))
        added = sorted(set(cur) - set(prev)); removed = sorted(set(prev) - set(cur))
        modified = sorted(k for k in set(cur) & set(prev) if cur[k] != prev[k])
        print("snapshot diff vs %s: +%d -%d ~%d" % (prevs[-1], len(added), len(removed), len(modified)))
        for k in added[:10]: print("  +", k)
        for k in removed[:10]: print("  -", k)
        for k in modified[:10]: print("  ~", k)
        return
    out = os.path.join(here, "manifest-%s.json" % today)
    json.dump({"date": today, "count": len(cur), "files": cur}, open(out, "w", encoding="utf-8"), indent=0)
    print("snapshot: %d leaves -> %s" % (len(cur), os.path.relpath(out, ROOT)))

if __name__ == "__main__":
    main()
