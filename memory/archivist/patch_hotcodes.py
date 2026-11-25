"""One-shot (2026-11-25): re-mint stale hot-note codes in MEMORY.md via mcode."""
import re
import sys

sys.path.insert(0, "memory/archivist")
import mcode

tbl = mcode.load_table()
pairs = [
    ("J351", "memory/ops/seat-matrix.json"),
    ("I623", "memory/mechanic/reboot-recovery.jsonl"),
    ("J290", "memory/ops/probes.md"),
    ("C134", "memory/designer/deep-sweep-2026-11-19.md"),
]
out = []
ok = True
for old, p in pairs:
    r = mcode.code_for(p, tbl)
    m = re.search(r":\s*([A-Z][a-z]?\d+)$", r)
    if not m:
        ok = False
        print("FAIL", p, r[:70])
        continue
    out.append((old, m.group(1)))
if not ok:
    sys.exit(1)
s = open("MEMORY.md", encoding="utf-8").read()
n = 0
for old, new in out:
    s, n2 = re.subn(r"\b" + old + r"\b", new, s)
    n += n2
open("MEMORY.md", "w", encoding="utf-8").write(s)
print(dict(out), "replaced", n, "size", len(s))
