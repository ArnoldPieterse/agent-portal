#!/usr/bin/env python3
# js_syntax_gate.py - Forge gate (spec: memory/ops/js-syntax-gate-spec-2026-11-26.md, owner Pixel)
#
# Pre-pin syntax gate for the portal UI JS files. Prevents recurrence of the
# 2026-11-25 core.js parse-fail incident (missing brace -> V8 'Unexpected end
# of input' -> whole portal UI frozen until a human hard-refreshed).
#
# Usage:
#   python memory/forge/js_syntax_gate.py                 # gate the default UI files
#   python memory/forge/js_syntax_gate.py <file.js> ...   # gate explicit files
#   --selftest   run acceptance test (healthy pass + broken-brace fail) in tempdir
#
# Exit codes: 0 = all pass, 1 = syntax failure detected (pin advance must be blocked),
#             2 = no parser available (neither node nor esprima).
#
# Parser strategy (spec alternative, since sandbox has no node):
#   1. `node --check` when a node binary exists (fastest, most faithful).
#   2. esprima (pure Python) with a string/comment/template-aware shim that
#      rewrites ES2020 `?.` -> `.` and `??` -> `||` (esprima 4.x predates them).
#      Shim preserves line/column, so reported error positions map to the source.
#
# Failures are appended to memory/ops/incidents.jsonl with file + line + col +
# stderr + surrounding context (spec acceptance #4: fixable without re-reading
# the whole file).

import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))          # .../memory/forge
ROOT = os.path.dirname(os.path.dirname(HERE))              # project root (script-relative, sandbox-proof)
DEFAULT_FILES = ["ui/core.js", "ui/uploads.js"]            # app.css is not JS; index.html is markup-only
INCIDENTS = os.path.join(ROOT, "memory", "ops", "incidents.jsonl")

# ---------------------------------------------------------------- parser probe
_NODE = None  # cached: path or None


def _find_node():
    global _NODE
    if _NODE is not None:
        return _NODE or None
    p = shutil.which("node")
    _NODE = p or ""
    return p


# ------------------------------------------------- esprima shim (ES2020 only)
# Single char-by-char pass with a small state machine so `?.`/`??` inside
# strings, template literal TEXT, and regex literals are never touched.
# Template interpolation ${...} is handled as code mode (shimmed there too).
# Line/column layout is preserved 1:1, so esprima error positions map to source.

NORMAL, SQ, DQ, TPL = 0, 1, 2, 3


def _rewrite_ops(src):
    out = []
    i, n = 0, len(src)
    state = NORMAL
    tpl_stack = []
    last_significant = ""
    while i < n:
        ch = src[i]
        if state == NORMAL:
            if ch in "'\"`:":
                if ch in "'\"":
                    state = SQ if ch == "'" else DQ
                    out.append(ch)
                    i += 1
                    continue
                tpl_stack.append(False)
                state = TPL
                out.append(ch)
                i += 1
                continue
            two = src[i:i + 2]
            if two == "??":
                out.append("||")
                last_significant = "|"
                i += 2
                continue
            if two == "?." and (i + 2 >= n or not src[i + 2].isdigit()):
                out.append(".")
                i += 2
                continue
            if ch in " \t\r\n":
                out.append(ch)
                i += 1
                continue
            if ch == "$" and i + 1 < n and src[i + 1] == "{":
                tpl_stack[-1] = True
                state = NORMAL
                last_significant = ch
                out.append(ch)
                i += 1
                continue
            last_significant = ch
            out.append(ch)
            i += 1
        elif state in (SQ, DQ):
            quote = "'" if state == SQ else '"'
            if ch == "\\":
                out.append(src[i:i + 2])
                i += 2
            elif ch == quote:
                out.append(ch)
                state = NORMAL
                last_significant = ch
                i += 1
            else:
                out.append(ch)
                i += 1
        elif state == TPL:
            in_interp = bool(tpl_stack) and tpl_stack[-1]
            if in_interp:
                if ch == "}":
                    tpl_stack[-1] = False
                    last_significant = ch
                elif ch == "$" and i + 1 < n and src[i + 1] == "{":
                    tpl_stack.append(True)
                out.append(ch)
                i += 1
            else:
                if ch == "\\":
                    out.append(src[i:i + 2])
                    i += 2
                elif ch == "$" and i + 1 < n and src[i + 1] == "{":
                    tpl_stack[-1] = True
                    out.append(ch)
                    i += 1
                elif ch == "`":
                    out.append(ch)
                    tpl_stack.pop()
                    if not tpl_stack:
                        state = NORMAL
                        last_significant = ch
                    else:
                        state = TPL
                    i += 1
                else:
                    out.append(ch)
                    i += 1
    return "".join(out)


def _parse_esprima(src, path):
    import esprima
    try:
        esprima.parseScript(_rewrite_ops(src), tolerant=False)
        return True, None
    except Exception as e:
        msg = str(e)
        line = col = None
        import re as _re
        m = _re.search(r"Line (\d+)(?::(\d+))?:", msg)
        if m:
            line, col = int(m.group(1)), int(m.group(2) or 0)
        return False, {"error": msg, "line": line, "col": col, "path": path}


def _parse_node(path):
    r = subprocess.run([_find_node(), "--check", path], capture_output=True, text=True, timeout=30)
    if r.returncode == 0:
        return True, None
    import re as _re
    line = col = None
    m = _re.search(r"(?:line|\()\s*(\d+)", r.stderr, _re.I)
    if m:
        line = int(m.group(1))
    return False, {"error": (r.stderr or r.stdout).strip()[:500], "line": line, "col": col, "path": path}


# ------------------------------------------------------------------- the gate

def _context(src, line, radius=2):
    if not line:
        return []
    ls = src.splitlines()
    lo = max(1, line - radius)
    hi = min(len(ls), line + radius)
    return ["%4d| %s" % (k, ls[k - 1]) for k in range(lo, hi + 1)]


def js_syntax_gate(files=DEFAULT_FILES, root=None):
    """Syntax-check each file. Returns list of per-file dicts; all ok => gate passes."""
    root = root or ROOT
    node = _find_node()
    results = []
    for rel in files:
        p = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            results.append({"file": rel, "ok": False, "parser": None,
                            "error": "file missing: %s" % p})
            continue
        t0 = time.perf_counter()
        if node:
            ok, err = _parse_node(p)
            parser = "node --check"
        else:
            src = open(p, encoding="utf-8").read()
            ok, err = _parse_esprima(src, rel)
            parser = "esprima+shim"
        ms = round((time.perf_counter() - t0) * 1000, 1)
        entry = {"file": rel, "ok": ok, "parser": parser, "ms": ms}
        if not ok and err:
            entry.update(err)
            entry["context"] = _context(open(p, encoding="utf-8").read(), err.get("line"))
        results.append(entry)
    return results


def gate_pass(results):
    return all(r["ok"] for r in results)


def record_incident(results, note="js-syntax-gate"):
    """Append failing files to memory/ops/incidents.jsonl (spec acceptance #4)."""
    bad = [r for r in results if not r["ok"]]
    if not bad:
        return 0
    os.makedirs(os.path.dirname(INCIDENTS), exist_ok=True)
    rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "type": "js-syntax-gate",
           "note": note, "fails": bad}
    with open(INCIDENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return len(bad)


# ------------------------------------------------------------------- selftest

def _selftest():
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        good = os.path.join(td, "good.js")
        open(good, "w", encoding="utf-8").write(
            "const a=[1,2,3];\n"          # healthy ES2020 usage must PASS
            "const b=a.map(x=>x?.id)??[];\n"
            "const s=`v=${a[0]?.toString()}`;\n"
            "const r=/a?b/g; const d=10/2; // x ?? y and a?.b in comment\n")
        broken = os.path.join(td, "broken.js")
        open(broken, "w", encoding="utf-8").write(
            "function f(){\n  if(true){\n    return 1;\n}\n)\n")   # missing } before )

        g = js_syntax_gate(["good.js", "broken.js"], root=td)
        by = {r["file"]: r for r in g}
        t1 = by["good.js"]["ok"] is True
        t2 = by["broken.js"]["ok"] is False and by["broken.js"].get("line") is not None
        total_ms = sum(r.get("ms", 0) for r in g)
        t3 = total_ms < 200
        print("good.js   :", "PASS" if t1 else "FAIL (should parse clean: %s)" % by["good.js"]) 
        print("broken.js :", "detected line=%s (%s)" % (by["broken.js"].get("line"), by["broken.js"].get("error", "")[:80]) if t2 else "FAIL (not detected)")
        print("cycle time: %.1fms (<200ms required: %s)" % (total_ms, "ok" if t3 else "SLOW"))
        ok = t1 and t2 and t3
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return _selftest()
    files = [a for a in argv if not a.startswith("-")] or DEFAULT_FILES
    results = js_syntax_gate(files)
    n_bad = record_incident(results) if not gate_pass(results) else 0
    for r in results:
        print("%s %s [%s] %sms%s" % ("OK  " if r["ok"] else "FAIL", r["file"],
              r.get("parser") or "-", r.get("ms", 0),
              "" if r["ok"] else " -> %s" % r.get("error", "")[:120]))
    print("gate: %d/%d pass%s" % (len(results) - n_bad, len(results),
          ", incident recorded to memory/ops/incidents.jsonl" if n_bad else ""))
    return 0 if gate_pass(results) else (1 if any(r.get("parser") for r in results) else 2)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
