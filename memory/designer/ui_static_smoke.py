#!/usr/bin/env python3
"""
ui_static_smoke.py - node-free static smoke check for portal ui/*.js modules.

Complements memory/builder/ui-tests/run.js (which needs Node, unavailable on this
sandbox host). This harness gives evidence NOW without a JS runtime by verifying:
  1. SYNTAX BALANCE  - braces {} / parens () / brackets [] balance in *code* mode
     after stripping line comments, block comments, 'strings', "strings" and
     template literals (with nested ${...} tracked so their code is still counted).
  2. EXPORT SURFACE  - each module exposes the global symbols its consumers rely on
     (window.UI / window.State / window.notify / window.Interactions / UMD exports),
     checked by source scan.

Exit 0 if every checked module passes both checks, else 1.
Writes a JSON measurement artifact next to this file when --json is passed or always.
"""
import os, sys, json, re, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "ui"))

# expected export symbols per module (regex over source). A PASS requires ALL present.
EXPECTED_EXPORTS = {
    "core.js":         [r"window\.UI\s*=\s*window\.UI\s*\|\|\s*\{\}", r"window\.__selftest\s*=", r"window\.__perf\s*=\s*\{\}"],
    "state.js":        [r"window\.State\s*=\s*\{\s*getState", r"setState", r"subscribe", r"seedState"],
    "api-client.js":   [r"module\.exports\s*=\s*factory\(\)", r"global\.apiClient\s*=\s*factory\(\)"],
    "icons.js":        [r"window\.UI\s*=\s*window\.UI\s*\|\|\s*\{\}", r"icon"],
    "uploads.js":      [r"jpost", r"startHeartbeat", r"stopHeartbeat"],
    "notifications.js":[r"window\.notify\s*=\s*function"],
    "interactions.js": [r"window\.Interactions\s*=\s*\{\s*initPress"],
    "components.js":   [r"root\.UI\s*=\s*\{\s*card", r"emptyState", r"errorState", r"loadingState", r"successToast"],
    "handoff.js":      [r"root\.UI\s*=\s*root\.UI\s*\|\|\s*\{\}\s*;", r"root\.UI\.handoffCard\s*=", r"root\.UI\.handoffList\s*="],
}

# modules to balance-check (all .js in ui/ except backup files)
_KEYWORDS = {"return", "typeof", "case", "in", "of", "new", "delete", "void", "throw", "do", "instanceof", "else", "yield", "await"}


def _prev_word(src, i):
    """Return the identifier/keyword immediately before index i (letters only), else ''."""
    j = i - 1
    while j >= 0 and src[j] in " \t\r\n":
        j -= 1
    word_end = j
    while j >= 0 and (src[j].isalpha() or src[j] in "_$"):
        j -= 1
    return src[j+1:word_end+1]


def scan_balance(src):
    """Single-pass tokenizer. Returns (ok, detail) where detail lists any imbalance.

    Tracks a frame stack. Each 'code' frame carries its OWN brace/paren/bracket counts so
    that a ${...} template interpolation only pops back to 'template' when ITS OWN brace
    count returns to zero. Template string-literal parts, comments and quoted strings are
    skipped; regex literals are detected via prior-token context and their bodies skipped.
    """
    n = len(src)
    i = 0
    line = 1
    in_line = False
    in_block = False
    in_str = None  # active quote char, if inside a single/double string
    prev_is_value = False  # True when the last significant token is value-ish (ident/num/string/) / ) / ])
    errors = []
    root = {"mode": "code", "bc": 0, "pc": 0, "kc": 0}
    frames = [root]
    while i < n:
        c = src[i]
        nxt = src[i+1] if i+1 < n else ""
        top = frames[-1]
        if c == "\n":
            line += 1
            in_line = False
            i += 1
            continue
        # comments (code mode only)
        if top["mode"] == "code" and not in_str:
            if c == "/" and nxt == "/":
                in_line = True; i += 2; prev_is_value = False; continue
            if c == "/" and nxt == "*":
                in_block = True; i += 2; prev_is_value = False; continue
        if in_block:
            if c == "*" and nxt == "/":
                in_block = False; i += 2; continue
            i += 1; continue
        if in_line:
            i += 1; continue
        # quoted strings (code mode)
        if top["mode"] == "code" and not in_str:
            if c in ("'", '"'):
                in_str = c; prev_is_value = False; i += 1; continue
            if c == "`":
                frames.append({"mode": "template"}); prev_is_value = False; i += 1; continue
            # division vs regex literal
            if c == "/":
                is_regex = (not prev_is_value) or (_prev_word(src, i) in _KEYWORDS)
                if is_regex:
                    i += 1  # skip opening /
                    in_class = False
                    while i < n and src[i] != "\n":
                        r = src[i]
                        if r == "\\":
                            i += 2; continue
                        if r == "[":
                            in_class = True
                        elif r == "]":
                            in_class = False
                        elif r == "/" and not in_class:
                            i += 1
                            break
                        i += 1
                    # consume flags [a-z]*
                    while i < n and src[i].isalpha():
                        i += 1
                    prev_is_value = True
                    continue
                # else: division operator, fall through (not a delimiter)
        if in_str:
            if c == "\\":
                i += 2; continue
            if c == in_str:
                in_str = None
                prev_is_value = True
            i += 1; continue
        # template literal string part -> skip until ${ or `
        if top["mode"] == "template":
            if c == "\\":
                i += 2; continue
            if c == "$" and nxt == "{":
                frames.append({"mode": "code", "bc": 0, "pc": 0, "kc": 0}); prev_is_value = False; i += 2; continue
            if c == "`":
                frames.pop(); prev_is_value = True; i += 1; continue
            i += 1; continue
        # code mode: count delimiters (per-frame) and update prev_is_value
        if c == "{":
            top["bc"] += 1; prev_is_value = False
        elif c == "(":
            top["pc"] += 1; prev_is_value = False
        elif c == "[":
            top["kc"] += 1; prev_is_value = False
        elif c == "}":
            if top["bc"] > 0:
                top["bc"] -= 1
            elif top is root:
                errors.append("line %d: unmatched '}'" % line)
            else:
                frames.pop()
            prev_is_value = False
        elif c == ")":
            if top["pc"] > 0:
                top["pc"] -= 1
            else:
                errors.append("line %d: unmatched ')'" % line)
            prev_is_value = True
        elif c == "]":
            if top["kc"] > 0:
                top["kc"] -= 1
            else:
                errors.append("line %d: unmatched ']'" % line)
            prev_is_value = True
        elif c.isalpha() or c in "_$":
            prev_is_value = True
        elif c.isdigit():
            prev_is_value = True
        elif c == ".":
            pass  # keep prior value-ish state (a.b / c stays division)
        elif c in "=+-*%<>!&|^~?:,;":
            prev_is_value = False
        i += 1
    for name, v in (("brace", root["bc"]), ("paren", root["pc"]), ("bracket", root["kc"])):
        if v != 0:
            errors.append("unclosed at EOF: %s=%d" % (name, v))
    if in_str is not None:
        errors.append("unterminated string at EOF")
    if len(frames) > 1:
        errors.append("unterminated template literal at EOF")
    return (len(errors) == 0, errors)


def main():
    results = []
    all_ok = True
    js_files = sorted(f for f in os.listdir(UI_DIR) if f.endswith(".js") and ".bak" not in f)
    for f in js_files:
        src = open(os.path.join(UI_DIR, f), encoding="utf-8", errors="replace").read()
        ok_bal, bal_errs = scan_balance(src)
        exp = EXPECTED_EXPORTS.get(f)
        missing = []
        if exp:
            for pat in exp:
                if not re.search(pat, src):
                    missing.append(pat)
        ok_exp = (exp is None) or (len(missing) == 0)
        ok = ok_bal and ok_exp
        all_ok = all_ok and ok
        results.append({
            "file": f,
            "lines": len(src.splitlines()),
            "balance_ok": ok_bal,
            "balance_errors": bal_errs,
            "exports_checked": bool(exp),
            "exports_missing": missing,
            "ok": ok,
        })
    report = {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "ui_dir": UI_DIR,
        "modules": len(js_files),
        "all_ok": all_ok,
        "results": results,
    }
    out_json = os.path.join(HERE, "ui_static_smoke_evidence.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    # console summary
    print("UI STATIC SMOKE  %s" % report["generated"])
    print("ui dir: %s" % UI_DIR)
    for r in results:
        flag = "PASS" if r["ok"] else "FAIL"
        extra = []
        if not r["balance_ok"]:
            extra.append("BALANCE:" + "; ".join(r["balance_errors"]))
        if r["exports_missing"]:
            extra.append("MISSING_EXPORTS:" + ", ".join(r["exports_missing"]))
        print("  [%s] %-20s lines=%-4d %s" % (flag, r["file"], r["lines"], " | ".join(extra)))
    print("SUMMARY: %d modules, all_ok=%s" % (len(js_files), all_ok))
    print("evidence: %s" % os.path.relpath(out_json))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
