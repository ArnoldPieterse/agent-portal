#!/usr/bin/env python3
"""Pixel - ui JS syntax gate (criterion #8 fallback, sandbox-safe).

No `node` / no pip in this seat, so we cannot run a real JS parser. This is a
tokenizer-aware brace/paren/bracket BALANCE check that correctly skips:
  - line + block comments
  - single/double-quoted strings (with escapes)
  - template literals (backticks, incl. nested ${ ... })
  - regex literals vs division (a `/` is a regex only when the previous token
    is an operator / opening-punct / keyword / start-of-input; otherwise it is
    division and must NOT open a literal).

Known limitation: balance != full syntax validity, but for this codebase it is a
strong smoke gate. Positive control: core.js + uploads.js were independently
proven parse-clean by Playwright/V8 (pageerrors []) on 2026-11-25, so any file
this tool flags that V8 accepts is a false positive to investigate here.

Exit 0 = all balanced; exit 1 = at least one imbalance.
"""
import pathlib, json, sys, datetime

KW = {"return","typeof","instanceof","in","of","new","delete","void","do",
      "else","yield","await","case","throw","if","while","for","switch"}

def prev_kind(out):
    """Classify the most recent emitted token char(s) in `out` (a compressed
    list of significant chars; whitespace/comments/strings already removed)."""
    if not out:
        return "end"
    k = len(out) - 1
    c = out[k]
    if c in "([{":
        return "open"
    if c in ")]}":
        return "close"
    if c.isalnum() or c in "_$":
        w = [c]; k -= 1
        while k >= 0 and (out[k].isalnum() or out[k] in "_.$"):
            w.append(out[k]); k -= 1
        word = "".join(reversed(w))
        return "kw" if word in KW else "id"
    return "op"  # , ; : = ? & | ! ~ + - * % etc -> regex allowed after these

def tokenize(t):
    out = []
    i, n = 0, len(t)
    while i < n:
        c = t[i]
        if c in " \t\r\n":
            i += 1; continue
        if c == "/" and i + 1 < n and t[i+1] == "/":
            j = t.find("\n", i)
            i = n if j < 0 else j; continue
        if c == "/" and i + 1 < n and t[i+1] == "*":
            j = t.find("*/", i + 2)
            i = n if j < 0 else j + 2; continue
        if c in "'\"":
            q = c; i += 1
            while i < n and t[i] != q:
                i += 2 if t[i] == "\\" else 1
            i += 1; out.append("s"); continue
        if c == "`":
            i += 1
            while i < n and t[i] != "`":
                if t[i] == "\\":
                    i += 2
                elif t[i] == "$" and i + 1 < n and t[i+1] == "{":
                    depth = 1; i += 2
                    while i < n and depth:
                        if t[i] == "{": depth += 1
                        elif t[i] == "}": depth -= 1
                        i += 1
                else:
                    i += 1
            i += 1; out.append("s"); continue
        if c == "/":
            pk = prev_kind(out)
            allowed = pk in ("op", "open", "kw", "end")
            if not allowed:
                out.append(c); i += 1; continue          # division
            nl = t.find("\n", i)
            j, k = i + 1, False
            while j < n and (nl < 0 or j < nl):
                cj = t[j]
                if cj == "\\":
                    j += 2; continue
                if cj == "[":
                    j += 1
                    while j < n and t[j] != "]":
                        j += 2 if t[j] == "\\" else 1
                    j += 1; continue
                if cj == "/":
                    k = True; break
                j += 1
            if not k:
                i += 1                                    # no same-line close -> treat as division
                continue
            i = j + 1; out.append("r"); continue          # regex literal consumed
        out.append(c)
        i += 1
    return out

def balance(toks):
    st = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for c in toks:
        if c in "([{":
            st.append(c)
        elif c in ")]}":
            if not st or st[-1] != pairs[c]:
                return False, f"mismatch '{c}'"
            st.pop()
    if st:
        return False, f"unclosed {st[-3:]}"
    return True, "ok"

if __name__ == "__main__":
    ui = pathlib.Path("ui")
    files = sorted(ui.glob("*.js"))
    res, fails = {}, []
    for f in files:
        t = f.read_text(encoding="utf-8")
        ok, msg = balance(tokenize(t))
        res[f.name] = {"ok": ok, "msg": msg, "lines": t.count("\n") + 1}
        if not ok:
            fails.append(f.name)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    out = {"ts": ts, "tool": "ui_syntax_gate.py (tokenizer-aware balance; NOT a full parser)",
           "total": len(files), "fails": fails,
           "positive_control": "core.js+uploads.js proven parse-clean by Playwright/V8 2026-11-25",
           "results": res}
    pathlib.Path("memory/pixel/ui-syntax-gate-2026-11-26.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(f"TS {ts} TOTAL {len(files)} FAILS {len(fails)} {fails}")
    for n in fails:
        print("  ", n, res[n]["msg"])
    sys.exit(0 if not fails else 1)
