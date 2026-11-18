#!/usr/bin/env python3
"""
token_lint.py - Design-token conformance gate for the live portal (ui/app.css).

Built 2026-11-19 by Builder to assist Designer goal #1 (Design Token System)
and goal #7 (Typography Hierarchy Audit). READ-ONLY on the CSS: it never
mutates app.css, so it cannot reintroduce the 2026-11-17 white-page regression
(cause = a second :root / light family overriding the canonical dark root).

Canonical rules encoded here (source: memory/portal/design-tokens.md):
  * Live production family = DARK, single authoritative :root in app.css.
  * Spacing scale: 4 / 8 / 12 / 16 / 24 px (documented exception: 14 toolbar gap).
  * Type ramp: base 15, h2 16, h3 12, mono 13, pills 11-13 px.

Checks (all grep-verifiable, no browser needed):
  C1 raw-hex-outside-root : #rgb/#rrggbb/#rrggbbaa appearing OUTSIDE any :root block
                            -> goal #1 wants 0 of these once components use var().
  C2 undefined-var         : var(--x) used but --x not defined in a :root block.
  C3 off-scale-font-size   : font-size value not on the canonical type ramp.
  C4 off-scale-spacing     : margin/padding/gap px value not on 4/8/12/16/24 (info).
  C5 root-count            : number of :root blocks (must stay 1 for live dark family).

Usage:
  python memory/designer/token_lint.py [path-to-css] [--json out.json]
Exit code: 0 if C1==0 and C2==0 and C3==0, else 1 (CI/gate friendly).
"""
import sys, re, json

DEFAULT_CSS = "ui/app.css"
SPACING_SCALE = {4, 8, 12, 16, 24}
SPACING_EXCEPTIONS = {14}      # documented toolbar-gap exception
TYPE_RAMP = {15, 16, 12, 13, 11, 14}   # base/h2/h3/mono/pills(11-13); 14 tolerated as body alt

def strip_comments_keep_lines(text):
    """Blank out /* ... */ interiors but preserve newlines so line numbers stay valid."""
    out = []
    i, n = 0, len(text)
    in_comment = False
    while i < n:
        c = text[i]
        if not in_comment and c == '/' and i + 1 < n and text[i+1] == '*':
            in_comment = True
            out.append('  ')
            i += 2
            continue
        if in_comment:
            if c == '*' and i + 1 < n and text[i+1] == '/':
                in_comment = False
                out.append('  ')
                i += 2
                continue
            out.append('\n' if c == '\n' else ' ')
            i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)

def line_of(offset, text):
    return text.count('\n', 0, offset) + 1

def find_token_scopes(masked):
    """Return spans of any {...} block whose body starts with a '--' assignment.
    Catches both the canonical ':root{--bg...}' AND override scopes like
    '[data-theme=light]{--bg...}' (the white-page regression landmine)."""
    scopes = []
    i = 0
    n = len(masked)
    while True:
        b = masked.find('{', i)
        if b < 0:
            break
        depth, j = 1, b + 1
        while j < n and depth > 0:
            if masked[j] == '{':
                depth += 1
            elif masked[j] == '}':
                depth -= 1
            j += 1
        body = masked[b+1:j-1]
        if body.lstrip().startswith('--'):
            prev = masked.rfind('}', 0, b)
            seltext = (masked[prev+1:b] if prev >= 0 else masked[:b]).strip()
            scopes.append({"selector": seltext[-70:], "start": b, "end": j,
                           "line": line_of(b, masked)})
        i = j
    return scopes

def analyze(path):
    raw = open(path, encoding='utf-8').read()
    masked = strip_comments_keep_lines(raw)

    # --- token-definition scopes (dark :root + any [data-theme=...] override) ---
    scopes = find_token_scopes(masked)
    dark_roots = [s for s in scopes if s["selector"].endswith(':root') or ':root' in s["selector"]]
    override_scopes = [s for s in scopes if s not in dark_roots]
    def inside_token_scope(pos):
        return any(s["start"] <= pos < s["end"] for s in scopes)

    # defined vars from the canonical DARK :root only (live family per ruling 2026-11-14)
    defined = {}
    for s in dark_roots:
        for name, val in re.findall(r'(--[a-zA-Z0-9-]+)\s*:\s*([^;{}]+)', masked[s["start"]:s["end"]]):
            defined[name] = val.strip()

    # C1 raw hex OUTSIDE every token-definition scope (genuine stray component values)
    hexes = []
    for m in re.finditer(r'#[0-9a-fA-F]{3,8}\b', masked):
        if not inside_token_scope(m.start()):
            ln = line_of(m.start(), masked)
            ctx = masked[max(0, m.start()-40):m.end()+20].replace('\n', ' ')
            hexes.append({"value": m.group(0), "line": ln, "ctx": ctx.strip()})

    # C2 undefined var refs
    used = set(re.findall(r'var\((--[a-zA-Z0-9-]+)', masked))
    undef = sorted(u for u in used if u not in defined)

    # C3 off-scale font-size
    fs = []
    for m in re.finditer(r'font-size:\s*([0-9.]+)px', masked):
        v = float(m.group(1))
        if v not in TYPE_RAMP:
            fs.append({"value": f"{m.group(1)}px", "line": line_of(m.start(), masked)})

    # C4 off-scale spacing (margin/padding/gap), informational
    sp = []
    for m in re.finditer(r'(margin|padding|gap)\s*:\s*([0-9.]+)px', masked):
        v = float(m.group(2))
        if v not in SPACING_SCALE and v not in SPACING_EXCEPTIONS:
            sp.append({"prop": m.group(1), "value": f"{m.group(2)}px", "line": line_of(m.start(), masked)})

    return {
        "file": path,
        "token_scope_count": len(scopes),
        "dark_root_count": len(dark_roots),
        "override_scopes": override_scopes,
        "defined_tokens": len(defined),
        "C1_raw_hex_outside_root": hexes,
        "C2_undefined_var_refs": undef,
        "C3_off_scale_font_size": fs,
        "C4_off_scale_spacing_info": sp,
    }

def main():
    args = [a for a in sys.argv[1:]]
    json_out = None
    if '--json' in args:
        i = args.index('--json')
        json_out = args[i+1]
        del args[i:i+2]
    path = args[0] if args else DEFAULT_CSS
    r = analyze(path)
    c1 = len(r["C1_raw_hex_outside_root"])
    c3 = len(r["C3_off_scale_font_size"])

    print(f"token_lint: {path}")
    ov = r["override_scopes"]
    flag = 'OK' if (r['dark_root_count'] == 1 and not ov) else 'WARN'
    print(f"  token-def scopes      : {r['token_scope_count']} (dark root x{r['dark_root_count']}, override x{len(ov)}) -> {flag}")
    for s in ov:
        print(f"       OVERRIDE SCOPE L{s['line']}: [{s['selector']}]  <- competing token family (white-page landmine)")
    print(f"  dark tokens defined   : {r['defined_tokens']}")
    print(f"  C1 raw hex outside root: {c1}   (goal #1 target: 0)")
    for h in r["C1_raw_hex_outside_root"][:40]:
        print(f"       L{h['line']:<4} {h['value']:<8} | ...{h['ctx']}...")
    if c1 > 40: print(f"       ... and {c1-40} more")
    undef = r["C2_undefined_var_refs"]
    print(f"  C2 undefined var refs  : {len(undef)}   (target: 0)")
    for u in undef[:40]:
        print(f"       {u}")
    print(f"  C3 off-scale font-size : {c3}   (goal #7 target: 0)")
    from collections import Counter
    fscount = Counter(f['value'] for f in r["C3_off_scale_font_size"])
    for v,c in sorted(fscount.items(), key=lambda x: float(x[0][:-2])):
        print(f"       {v:<8} x{c}")
    print(f"  C4 off-scale spacing   : {len(r['C4_off_scale_spacing_info'])} (informational)")

    if json_out:
        json.dump(r, open(json_out, 'w', encoding='utf-8'), indent=2)
        print(f"  JSON written -> {json_out}")

    ok = (c1 == 0 and len(undef) == 0 and c3 == 0)
    print(f"\nRESULT: {'PASS' if ok else 'NEEDS-WORK'}")
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
