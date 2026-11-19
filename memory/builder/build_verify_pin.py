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

# Tokens after which a '/' begins a regex literal (not division).
_REGEX_PREV = set("=(,:[!&|?{};+-*%~^<> \\t\\n\\rreturn typeof case")

def _js_balanced(src):
    """Char-scanner for JS delimiter balance. Handles line/block comments,
    single/double/template strings (with nested ${...} frames) and best-effort
    regex literals. Returns (ok, msg). Not a full parser - catches genuine
    unbalanced delimiters introduced by hand edits; template/regex false-positives
    of the old regex-strip heuristic are eliminated."""
    stack = []          # code-mode delimiter stack
    tmpl = []           # template ${ } frames: True when inside an interpolation
    state = "code"      # code | line | block | sq | dq | tpl
    i, n = 0, len(src)
    prev_sig = ""       # last significant token tail (for regex detection)
    def push(c):
        if c in "({[": stack.append(c)
        elif c in ")}]":
            want = {")":"(","}":"{","]":"["}[c]
            if not stack or stack[-1] != want:
                return False
            stack.pop()
        return True
    while i < n:
        ch = src[i]; nxt = src[i+1] if i+1 < n else ""
        if state == "code":
            if ch == "/" and nxt == "/": state="line"; i+=2; continue
            if ch == "/" and nxt == "*": state="block"; i+=2; continue
            if ch == "'": state="sq"; prev_sig="str"; i+=1; continue
            if ch == '"': state="dq"; prev_sig="str"; i+=1; continue
            if ch == "`":
                # template literal: scan to matching backtick, honour ${ } + nested templates
                j = i+1; depth = 0; in_interp = False
                while j < n:
                    c2 = src[j]; nx2 = src[j+1] if j+1<n else ""
                    if in_interp:
                        if c2 == "{": depth+=1
                        elif c2 == "}":
                            depth-=1
                            if depth==0: in_interp=False
                        elif c2 == "`":  # nested template inside interpolation
                            # find its closing backtick (naive, escapes only)
                            k=j+1
                            while k<n and src[k]!="`":
                                if src[k]=="\\": k+=1
                                k+=1
                            j=k; 
                        elif c2=="'":
                            k=j+1
                            while k<n and src[k]!="'":
                                if src[k]=="\\": k+=1
                                k+=1
                            j=k
                        elif c2=='"':
                            k=j+1
                            while k<n and src[k]!='"':
                                if src[k]=="\\": k+=1
                                k+=1
                            j=k
                    else:
                        if c2=="\\": j+=1
                        elif c2 == "$" and nx2 == "{": in_interp=True; depth=0
                        elif c2 == "`": break
                    j+=1
                i = j+1; prev_sig="str"; continue
            if ch == "/":
                # possible regex: previous significant char suggests expression start
                p = prev_sig[-1] if prev_sig else ""
                if p in "=(,:[!&|?{};+-*%~^>" or prev_sig in ("return","typeof","case"):
                    j=i+1
                    while j<n and src[j]!="/":
                        if src[j]=="\\": j+=1
                        elif src[j]=="\n": break  # not a regex after all
                        j+=1
                    i=j+1; prev_sig="str"; continue
                else:
                    i+=1; prev_sig="op"; continue
            if ch in "({[]})":
                if not push(ch):
                    return False, f"unbalanced {ch} at offset {i}"
                prev_sig = ch
            elif ch == ";" or ch == "\n": prev_sig = ch
            elif ch in " \t\r": pass
            else: prev_sig = ch
            i+=1; continue
        elif state == "line":
            if ch=="\n": state="code"
            i+=1; continue
        elif state == "block":
            if ch=="*" and nxt=="/": state="code"; i+=2; continue
            i+=1; continue
        elif state in ("sq","dq"):
            q = "'" if state=="sq" else '"'
            if ch=="\\": i+=2; continue
            if ch==q: state="code"; prev_sig="str"
            i+=1; continue
        elif state == "tpl":
            # (unused - templates handled inline above) keep for safety
            i+=1; continue
    if stack:
        return False, f"unclosed {stack[-1]} ({len(stack)} open at EOF)"
    return True, f"delimiter balance OK ({len(src)} chars scanned) [scanner: node-free]"

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
        # char-scanner: template/regex/comment aware (node not available in sandbox)
        s = data.decode("utf-8","replace")
        ok2, msg2 = _js_balanced(s)
        return ok2, msg2
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
