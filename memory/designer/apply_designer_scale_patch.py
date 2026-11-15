#!/usr/bin/env python3
"""Designer goal #4 - 4px spacing scale + type scale for index.html (2026-11-15, REBUILT after mirror clobber).

Idempotent, guarded transform. Accepts TWO bases (order-independent w.r.t. #3):
  a) pristine pin sha12 37549a041412 -> the 3 goal-#3 acc-deep byte replacements
     (from apply_acc_deep_patch.py, subsumed here) are applied first; or
  b) post-goal#3 pin sha12 1cc852c98c5a -> proceeds directly.
NOTE: this shared-folder copy of index.html is CLOBBERED by the 5-min White->shared
SMB mirror (observed 2026-11-15 twice this round). Run against a STAGED copy for
verification, and on WHITE's live portal root for the real apply.

:root additions (values preserved = zero visual shift for radii/sacred dims):
  spacing --sp-1..8  = 4/8/12/16/20/24/32/40 px
  type    --fs-xs..3xl = 11/12/13/14/15/16/18/22 px
  radius  --r-sm/md/lg/xl = 6/8/10/14 px
  layout  --w-aside:250px, --gtile-minw:170px (documented constants)
Transforms:
  font-size:Npx (N in type map) -> var(--fs-*); display sizes 70->72 / 90->92 px
  border-radius:{6,8,9,10,14}px -> --r-sm/md/lg/xl (9 snapped to 8 = --r-md)
  margin*/padding*/gap/top/bottom/left/right values -> nearest 4px multiple,
    ties round UP, then tokenized when on the sp scale (micro 1/2/3px kept literal)
  width/height/min-*/max-* off-grid values snapped to grid (9->8,18->20,26->28);
    250px(width)->var(--w-aside), 170px(min-width)->var(--gtile-minw); rest untouched
  font shorthand (Npx/LH family) expanded to explicit font-size/line-height/font-family
Gate (must all pass, else abort without writing):
  strip :root -> every remaining px literal is {1,2,3} or a multiple of 4
  every var(--X) referenced is defined in :root; braces balanced; no 'font:' shorthand left
Usage: python apply_designer_scale_patch.py [path-to-index.html]   (default: beside script)
"""
import hashlib, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = sys.argv[1] if len(sys.argv) > 1 else "index.html"
PRISTINE_SHA = "37549a041412"   # canonical pin (L827 dup-catch fixed)
POST3_SHA = "1cc852c98c5a"      # pristine + goal-#3 acc-deep
MARKER = "--sp-1:4px"
ACC_DEEP = [
    (b"--acc:#4f8cff;--ok:#3ddc84;", b"--acc:#4f8cff;--acc-deep:#2563eb;--ok:#3ddc84;"),
    (b"#send{background:var(--acc);border:none;color:#fff;",
     b"#send{background:var(--acc-deep);border:none;color:#fff;"),
    (b".btn.pri{background:var(--acc);border-color:var(--acc);color:#fff}",
     b".btn.pri{background:var(--acc-deep);border-color:var(--acc);color:#fff}"),
]

def sha12(p): return hashlib.sha1(open(p, "rb").read()).hexdigest()[:12]

text = open(PATH, encoding="utf-8", newline="").read()
cur = sha12(PATH)
if MARKER in text:
    print(f"already applied (marker present), current sha12={cur} - nothing to do.")
    sys.exit(0)
if cur == PRISTINE_SHA:
    data = open(PATH, "rb").read()
    for old, new in ACC_DEEP:
        if data.count(old) != 1:
            print(f"ABORT: acc-deep anchor {old[:40]!r} count={data.count(old)} != 1")
            sys.exit(1)
        data = data.replace(old, new)
    open(PATH, "wb").write(data)
    text = data.decode("utf-8")
    print(f"base was pristine {PRISTINE_SHA}; applied goal-#3 acc-deep 3/3 -> {sha12(PATH)}")
elif cur != POST3_SHA:
    print(f"ABORT: base sha12 {cur} not in {{{PRISTINE_SHA}, {POST3_SHA}}}. Re-baseline with Designer.")
    sys.exit(1)

log = []
def sub(pattern, repl, count_expect=None, label=""):
    global text
    new, n = re.subn(pattern, repl, text)
    if count_expect is not None and n != count_expect:
        print(f"ABORT[{label}]: expected {count_expect} matches, got {n}")
        sys.exit(1)
    text = new
    log.append((label or pattern, n))

# 1) :root scale tokens (anchor unique)
TOKENS = ("--sp-1:4px;--sp-2:8px;--sp-3:12px;--sp-4:16px;--sp-5:20px;--sp-6:24px;"
          "--sp-7:32px;--sp-8:40px;--fs-xs:11px;--fs-sm:12px;--fs-md:13px;--fs-base:14px;"
          "--fs-lg:15px;--fs-xl:16px;--fs-2xl:18px;--fs-3xl:22px;--r-sm:6px;--r-md:8px;"
          "--r-lg:10px;--r-xl:14px;--w-aside:250px;--gtile-minw:170px;")
assert text.count("--faint:#8b98ab;") == 1
text = text.replace("--faint:#8b98ab;", "--faint:#8b98ab;" + TOKENS)
log.append((":root scale tokens inserted", 1))

# 2) font shorthand -> explicit props (body, .opsbox, #actBody)
FS = {"11":"xs","12":"sm","13":"md","14":"base","15":"lg","16":"xl","18":"2xl","22":"3xl"}
def font_shorthand(m):
    size, lh, fam = m.group(1).removesuffix("px"), m.group(2), m.group(3).strip()
    return f"font-size:var(--fs-{FS[size]});line-height:{lh};font-family:{fam}"
sub(r"font:(\d+(?:\.\d+)?px)/([\d.]+)\s*([^;{}]+?)(?=[;}])", font_shorthand, 3, "font-shorthand expansion")

# 2b) quote-aware pass: inline style="..." attrs + JS cssText="..." strings
#     (the global passes below assume ; / } terminators, which do not exist in attr values)
FSX = dict(FS); FSX["10"] = "xs"   # JS chip font-size 10px -> --fs-xs (11px): smallest declared type step
def conv_decl(d):
    mm = re.match(r"^([a-z-]+)\s*:\s*(.+)$", d, re.S)
    if not mm: return d
    prop, val = mm.group(1), mm.group(2).strip()
    single = re.match(r"^(\d+(?:\.\d+)?)px$", val)
    if prop == "font-size" and single:
        n = int(single.group(1))
        if str(n) in FSX: return f"font-size:var(--fs-{FSX[str(n)]})"
        if n in (70, 90): return f"font-size:{(n + 2) // 4 * 4}px"
        return d
    if prop == "border-radius" and single and single.group(1) in RAD:
        return f"border-radius:var(--r-{RAD[single.group(1)]})"
    if re.match(r"^(margin|padding|gap|top|bottom|left|right)(-[a-z]+)?$", prop):
        out = []
        for v in val.split():
            vm = re.match(r"^(\d+(?:\.\d+)?)px$", v)
            if not vm: out.append(v); continue
            s2 = snap(vm.group(1)) or vm.group(1)
            tok = SP.get(s2)
            out.append(f"var(--{tok})" if tok else s2 + "px")
        return prop + ":" + " ".join(out)
    if re.match(r"^(width|height|min-width|min-height|max-width|max-height)$", prop):
        out = []
        for v in val.split():
            vm = re.match(r"^(\d+(?:\.\d+)?)px$", v)
            if not vm: out.append(v); continue
            n = int(vm.group(1))
            if prop == "width" and n == 250: out.append("var(--w-aside)")
            elif prop == "min-width" and n == 170: out.append("var(--gtile-minw)")
            else:
                k = (n + 2) // 4 * 4; out.append(f"{k}px" if k != n else v)
        return prop + ":" + " ".join(out)
    return d
ATTR_RE = r'(?:style|cssText)="([^"]*)"'
def conv_attr(m):
    decls = [d for d in m.group(1).split(";") if d.strip()]
    return '"' + ";".join(conv_decl(d) for d in decls) + '"'
text, n_attr = re.subn(ATTR_RE, conv_attr, text)
log.append(("inline style/cssText attrs (quote-aware)", n_attr))

# 3) font-size longhand -> type tokens (CSS + inline attrs + JS templates)
def fs_map(m): return f"font-size:var(--fs-{FS[m.group(1)]})"
sub(r"font-size:(11|12|13|14|15|16|18|22)px", fs_map, None, "font-size -> --fs-*")
# display sizes off the text scale: snap to grid (70->72, 90->92); 32 already on grid
sub(r"font-size:70px", "font-size:72px", None, "display size 70->72")
sub(r"font-size:90px", "font-size:92px", None, "display size 90->92")

# 4) border-radius -> radius tokens (9 snapped to 8 = --r-md)
RAD = {"6":"sm","8":"md","9":"md","10":"lg","14":"xl"}
def rad_map(m): return f"border-radius:var(--r-{RAD[m.group(1)]})"
sub(r"border-radius:(6|8|9|10|14)px", rad_map, None, "border-radius -> --r-*")

# 5) rhythm spacing (margin*/padding*/gap/top/bottom/left/right) -> sp tokens / grid
SP = {"4":"sp-1","5":"sp-1","6":"sp-2","7":"sp-2","8":"sp-2","9":"sp-2",
      "10":"sp-3","12":"sp-3","13":"sp-3","14":"sp-4","16":"sp-4","18":"sp-5"}
def snap(v):
    if v in ("1","2","3"): return None            # documented micro, keep literal
    n = int(v)
    k = (n + 2) // 4 * 4                            # nearest 4px multiple, ties round UP (no banker's rounding)
    return str(k) if k != n else v
RHYTHM_RE = r"(?<![\w-])(margin|padding|gap|top|bottom|left|right)(-[a-z]+)?\s*:\s*([^;{}]+)"
def rhythm_sub(m):
    vals = m.group(3).split()
    out = []
    for v in vals:
        mm = re.match(r"^(\d+(?:\.\d+)?)px$", v)
        if not mm: out.append(v); continue
        s = snap(mm.group(1)) or mm.group(1)
        tok = SP.get(s)
        out.append(f"var(--{tok})" if tok else s + "px")
    return f"{m.group(1)}{m.group(2) or ''}:{' '.join(out)}"
sub(RHYTHM_RE, rhythm_sub, None, "rhythm spacing -> --sp-* / grid")

# 6) fixed dims: snap off-grid; sacred values tokenized
DIM_RE = r"(?<![\w-])(width|height|min-width|min-height|max-width|max-height)\s*:\s*([^;{}]+)"
def dim_sub(m):
    vals = m.group(2).split()
    out = []
    for v in vals:
        mm = re.match(r"^(\d+(?:\.\d+)?)px$", v)
        if not mm: out.append(v); continue
        n = int(mm.group(1))
        if m.group(1) == "width" and n == 250: out.append("var(--w-aside)")
        elif m.group(1) == "min-width" and n == 170: out.append("var(--gtile-minw)")
        else:
            k = (n + 2) // 4 * 4; out.append(f"{k}px" if k != n else v)
    return f"{m.group(1)}:{' '.join(out)}"
sub(DIM_RE, dim_sub, None, "fixed dims snapped/tokenized")

# 7) GATE (on transformed text)
import os as _os
if "DESIGNER_DEBUG" in _os.environ:
    open("memory/designer/staged/debug_out.html", "w", encoding="utf-8", newline="").write(text)
style = re.search(r"<style>(.*?)</style>", text, re.S).group(1)
css_noroot = re.sub(r":root\{.*?\}", "", style, flags=re.S)
bad = []
for m in re.finditer(r"(\d+(?:\.\d+)?)px", css_noroot):
    v = float(m.group(1))
    if v not in (1,2,3) and v % 4 != 0: bad.append(m.group(0))
# px outside <style> (inline attrs / JS templates)
outside = re.sub(r"<style>.*?</style>", "", text, flags=re.S)
for m in re.finditer(r"(\d+(?:\.\d+)?)px", outside):
    v = float(m.group(1))
    if v not in (1,2,3) and v % 4 != 0: bad.append("outside:" + repr(outside[max(0,m.start()-60):m.end()+30]))
if bad: print("ABORT[gate]: off-scale px:", bad[:20]); sys.exit(1)
root = re.search(r":root\{(.*?)\}", style, re.S).group(1)
defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", root))
used = set(re.findall(r"var\((--[a-z0-9-]+)\)", text))
if not used <= defined: print("ABORT[gate]: undefined vars:", sorted(used - defined)); sys.exit(1)
if style.count("{") != style.count("}"): print("ABORT[gate]: unbalanced braces"); sys.exit(1)
if re.search(r"font\s*:\s*[\d.]+px", text): print("ABORT[gate]: font shorthand remains"); sys.exit(1)
for k in ("#send{background:var(--acc-deep);", ".btn.pri{background:var(--acc-deep);"):
    if k not in text: print(f"ABORT[gate]: goal#3 fill lost: {k}"); sys.exit(1)

open(PATH, "w", encoding="utf-8", newline="").write(text)
print("applied scale transform; changes by category:")
for label, n in log: print(f"  {n:>4}x  {label}")
print(f"GATE PASS: no off-scale px outside :root; all vars defined; braces balanced; #3 fills intact.")
print(f"NEW PIN sha12 = {sha12(PATH)}  (size {os.path.getsize(PATH)} B)")
