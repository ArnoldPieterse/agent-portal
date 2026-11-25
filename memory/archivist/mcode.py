"""mcode.py - M-CODE memory address resolution (2026-11-25, Archivist).

A code is [A-Z][a-z]?\d+ : the uppercase letter names a module folder under
memory/, an optional lowercase letter names a subfolder of that module, and the
digits are the file number N. The legend table sits in MEMORY.md between the
MCODE markers; this script is the reference implementation of that formula.

Resolve rule: key -> folder F from the table. If F/INDEX.md has lines containing
an arrow to a target, the code resolves to the Nth (1-based) such target; else
to the Nth regular file in sorted(F), dotfiles and INDEX.md excluded.

Usage:
  python mcode.py A7 Ja2 La5     resolve codes, print path plus summary
  python mcode.py --check        validate table vs disk, exit 1 on dangling key
  python mcode.py --encode PATH  reverse lookup: print the code for a file
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEMORY_MD = os.path.join(ROOT, "MEMORY.md")
CODE_RE = re.compile(r"^([A-Z])([a-z]?)(\d+)$")
ARROW_RE = re.compile(r"->\s*(\S+)")
def load_table():
    raw = open(MEMORY_MD, encoding="utf-8").read()
    span = re.search(r"MCODE:BEGIN -->(.*?)<!-- MCODE:END", raw, re.S)
    if span is None:
        sys.exit("mcode: MEMORY.md has no MCODE block")
    table = {}
    for tok in re.split(r"[,\n]", span.group(1)):
        tok = tok.strip()
        if "|" in tok:
            k, v = tok.split("|", 1)
            table[k.strip()] = v.strip().replace("\\", "/")
    return table


def arrow_lines(folder):
    p = os.path.join(ROOT, folder.replace("/", os.sep), "INDEX.md")
    out = []
    if not os.path.isfile(p):
        return out
    for line in open(p, encoding="utf-8", errors="replace"):
        m = ARROW_RE.search(line)
        if m:
            tgt = m.group(1).strip("`*'")
            rest = re.sub(r"\s{2,}", " ", line[m.end():].strip())[:80]
            out.append((tgt, rest))
    return out
def list_files(folder):
    parts = (ROOT,) + tuple(folder.split("/"))
    d = os.path.join(*parts)
    if not os.path.isdir(d):
        return []
    names = sorted(f for f in os.listdir(d)
                   if os.path.isfile(os.path.join(d, f))
                   and not f.startswith(".") and f != "INDEX.md")
    return [folder + "/" + f for f in names]


def resolve(code, table):
    hit = CODE_RE.match(code)
    if not hit:
        return "%-6s not a code (pattern [A-Z][a-z]?\d+)" % code
    top = hit.group(1)
    sub = hit.group(2)
    num = int(hit.group(3))
    folder = table.get(top)
    if folder is None:
        return "%-6s unknown module letter %r" % (code, top)
    if sub:
        child = table.get(top + sub)
        if child is None or not child.startswith(folder + "/"):
            return "%-6s unknown subfolder key %r" % (code, top + sub)
        folder = child
    entries = list(arrow_lines(folder))
    if entries:
        if num > len(entries):
            return "%-6s out of range (%d in %s)" % (code, len(entries), folder)
        tgt, summ = entries[num - 1]
        return "%-6s %s%s" % (code, tgt, "   " + summ if summ else "")
    files = list_files(folder)
    if num > len(files):
        return "%-6s out of range (%d in %s)" % (code, len(files), folder)
    return "%-6s %s" % (code, files[num - 1])
def code_for(path, table):
    norm = path.replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]
    pick = None
    for key, val in sorted(table.items(), key=lambda kv: -len(kv[1])):
        if len(key) <= 2 and (norm == val or norm.startswith(val + "/")):
            pick = (key, val)
            break
    if pick is None:
        return "%s : not under any lettered folder" % norm
    key, folder = pick
    for idx, (tgt, _s) in enumerate(arrow_lines(folder), 1):
        t2 = tgt.replace("\\", "/")
        same = t2 == norm or (t2.startswith(folder + "/")
                              and os.path.basename(t2) == os.path.basename(norm))
        if same:
            return "%s : %s%d" % (norm, key, idx)
    files = list_files(folder)
    if norm in files:
        return "%s : %s%d" % (norm, key, files.index(norm) + 1)
    return "%s : under %s but not listed there" % (norm, folder)


def audit_table(table):
    problems = 0
    for key in sorted(table):
        val = table[key]
        d = os.path.join(ROOT, *val.split("/"))
        if not os.path.isdir(d):
            print("DANGLING %s -> %s (no such dir)" % (key, val))
            problems += 1
        elif len(key) == 2 and key[0] in table:
            if not val.startswith(table[key[0]] + "/"):
                print("NOT-CHILD %s -> %s (not under %s)" % (key, val, table[key[0]]))
                problems += 1
    tops = set(v for k, v in table.items() if len(k) == 1)
    memdir = os.path.join(ROOT, "memory")
    for name in sorted(os.listdir(memdir)):
        full = os.path.join(memdir, name)
        if (os.path.isdir(full) and not name.startswith(("_", "."))
                and ("memory/" + name) not in tops):
            print("UNLETTERED memory/%s (advisory only)" % name)
    print("mcode --check: %d keys, %d dangling" % (len(table), problems))
    return 1 if problems else 0
def cli(argv):
    if not argv:
        print(__doc__.strip())
        return 0
    tbl = load_table()
    if argv[0] == "--check":
        return audit_table(tbl)
    if argv[0] == "--encode":
        for one in argv[1:]:
            print(code_for(one, tbl))
        return 0
    for one in argv:
        print(resolve(one, tbl))
    return 0


if __name__ == "__main__":
    sys.exit(cli(sys.argv[1:]))
