#!/usr/bin/env python3
"""build_verify_pin.py - validate -> sha12 -> canonical backup -> pin-advance report.

Cycle-7 Builder Goal #3 (build-verify-pin pipeline), increment 1: the pin-clobber
prevention leg. Safe by default (dry-run); only edits memory_mirror.py with --apply.

Usage:
  python memory/builder/build_verify_pin.py <file> [--apply MIRROR] [--date YYYY-MM-DD] [--rev a]

Steps:
  (a) validate syntax      .html / .css / .js (JS is a delimiter-balance heuristic when node is absent)
  (b) compute sha12        first 12 hex of sha1(file bytes)
  (c) write canonical copy memory/designer/<stem>_CANONICAL_<sha12>_<date><rev>.<ext>
  (d) pin-advance report   exact PIN_FILES line for memory_mirror.py

Exit: 0 ok | 2 validation failed | 3 file not found | 4 --apply target problem
"""
import os, re, hashlib, sys, datetime, shutil
from html.parser import HTMLParser

def sha12(b): return hashlib.sha1(b).hexdigest()[:12]

class _HP(HTMLParser):
    def __init__(self): super().__init__(); self.n=0; self.err=None
    def handle_starttag(self,t,a): self.n+=1
    def error(self,m): self.err=m

def validate(path, data):
    ext = os.path.splitext(path)[1].lower()
    if not data.strip():
        return False, "file is empty/whitespace"
    if ext == ".html":
        p=_HP(); 
        try: p.feed(data.decode("utf-8","replace"))
        except Exception as e: return False, f"HTML parse error: {e}"
        if p.err: return False, f"HTML error: {p.err}"
        low = data[:2048].decode("utf-8","replace").lower()
        if "<html" not in low and "<!doctype" not in low:
            return True, f"parsed {p.n} elements (no <html>/<doctype> header - check)"
        return True, f"parsed {p.n} elements OK"
    if ext == ".css":
        s = re.sub(r"/\*.*?\*/", "", data.decode("utf-8","replace"), flags=re.S)
        for op,cl in [("{","}"),("(",")")]:
            if s.count(op)!=s.count(cl):
                return False, f"unbalanced {op}{cl}: {s.count(op)} vs {s.count(cl)}"
        return True, f"braces/parens balanced ({s.count('{')} rules)"
    if ext == ".js":
        # strip strings + comments, then check delimiter balance (node not available in sandbox)
        s = data.decode("utf-8","replace")
        s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
        s = re.sub(r"(?m)//[^\n]*", "", s)
        s = re.sub(r"'(\\.|[^'\\])*'", "''", s)
        s = re.sub(r'"(\\.|[^"\\])*"', '""', s)
        s = re.sub(r"`(\\.|[^`\\])*`", "``", s)
        for op,cl in [("{","}"),("[","]"),("(",")")]:
            if s.count(op)!=s.count(cl):
                return False, f"unbalanced {op}{cl}: {s.count(op)} vs {s.count(cl)} (heuristic)"
        return True, f"delimiter balance OK ({s.count('{')} blocks) [heuristic: node unavailable]"
    return True, "no validator for this extension - skipped"

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h","--help"):
        print(__doc__); return 0
    path = args[0]
    apply_mirror = date = rev = None
    i=1
    while i < len(args):
        if args[i]=="--apply": apply_mirror=args[i+1]; i+=2
        elif args[i]=="--date": date=args[i+1]; i+=2
        elif args[i]=="--rev": rev=args[i+1]; i+=2
        else: print(f"WARN unknown arg {args[i]}"); i+=1
    if not os.path.exists(path):
        print(f"FAIL(3): file not found: {path}"); return 3
    date = date or datetime.date.today().isoformat()
    rev = (rev or "a")
    data = open(path,"rb").read()

    # (a) validate
    ok, msg = validate(path, data)
    print(f"[a] validate {path}: {'OK' if ok else 'FAIL'} - {msg}")
    if not ok: return 2

    # (b) sha12
    h = sha12(data)
    print(f"[b] sha12 = {h}   ({len(data)} bytes)")

    # (c) canonical copy
    base = os.path.basename(path).replace(".","_")   # index.html -> index_html (documented pin convention)
    ext = os.path.splitext(path)[1] or ".txt"
    dest_dir = "memory/designer"
    os.makedirs(dest_dir, exist_ok=True)
    dest = f"{dest_dir}/{base}_CANONICAL_{h}_{date}{rev}{ext}"
    shutil.copyfile(path, dest)
    print(f"[c] canonical copy -> {dest} ({os.path.getsize(dest)} bytes)")

    # (d) pin-advance report
    print("[d] PIN_FILES update for memory_mirror.py (match your schema):")
    print(f'    "{os.path.basename(path)}": ("{h}", "{dest}")')
    if apply_mirror:
        if not os.path.exists(apply_mirror) or os.path.getsize(apply_mirror)==0:
            print(f"FAIL(4): --apply target missing/empty: {apply_mirror} (dry-run only; relay real schema)")
            return 4
        src = open(apply_mirror,encoding="utf-8").read()
        pat = re.compile(r'("?\%s"?\s*:\s*\()[^)]*(\))' % re.escape(os.path.basename(path)))
        if pat.search(src):
            new = pat.sub(lambda m: f'{m.group(1)}"{h}", "{dest}"{m.group(2)}', src)
            open(apply_mirror,"w",encoding="utf-8").write(new)
            print(f"    applied -> {apply_mirror}")
        else:
            print(f"    no existing entry for {os.path.basename(path)} in {apply_mirror}; append the line above")
    return 0

if __name__=="__main__":
    sys.exit(main())
