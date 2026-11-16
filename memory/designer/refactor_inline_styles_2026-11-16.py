#!/usr/bin/env python3
"""Goal #3 (component abstraction): eliminate static inline style="" from chat/panel
form elements in index.html by extracting named component + utility classes.
Idempotent: safe to re-run; no-op if already applied. Preserves exact computed values.
"""
import re, hashlib, sys

PATH = r"index.html"
txt = open(PATH, "rb").read().decode("utf-8", errors="replace")
orig_bytes = len(txt.encode("utf-8"))
log = []

# ---------- 1. Insert the named-class CSS block (once) ----------
SENTINEL = "/* COMPONENT CLASSES v1 (goal #3) */"
CSS_RULES = [
    ".c-err{color:var(--err)}",
    ".btn-refresh{margin-left:auto;padding:2px 10px;font-size:var(--fs-12)}",
    ".subhead{font-size:var(--fs-12);color:var(--dim)}",
    ".opsrow--stretch{align-items:stretch}",
    ".opsbox--fill{flex:1;max-height:none}",
    ".input-bar{height:32px;padding:2px}",
    ".btn-h30{height:30px}",
    ".mt6{margin-top:6px}.mt8{margin-top:8px}",
    ".mb4{margin-bottom:4px}.mb6{margin-bottom:6px}.mb8{margin-bottom:8px}",
    ".w70{max-width:70px}.w90{max-width:90px}",
    ".input-auto{width:auto}",
    ".fs-12{font-size:var(--fs-12)}",
    ".hidden{display:none}",
]
CSS = "<style id=\"component-classes\">" + SENTINEL + chr(10) + chr(10).join(CSS_RULES) + chr(10) + "</style>"
if SENTINEL in txt:
    log.append("css block already present (skip insert)")
else:
    idx = txt.find("</head>")
    assert idx != -1, "no </head>"
    txt = txt[:idx] + CSS + chr(10) + txt[idx:]
    log.append("inserted component-classes <style> before </head>")

# ---------- 2. Helper: strip a specific inline style attr, merge class ----------
def strip_style(html, tag, style_val, add_class):
    pat = re.compile(r'(<%s\b)([^>]*?)(>)' % re.escape(tag), re.DOTALL)
    cnt = {"n": 0}
    def repl(m):
        open_, attrs, close = m.group(1), m.group(2), m.group(3)
        sattr = re.search(r'\sstyle\s*=\s*"([^"]*)"', attrs)
        if not sattr or sattr.group(1) != style_val:
            return m.group(0)
        newattrs = attrs[:sattr.start()] + attrs[sattr.end():]
        cattr = re.search(r'\sclass\s*=\s*"([^"]*)"', newattrs)
        if cattr:
            newcls = (cattr.group(1) + " " + add_class).strip()
            newattrs = newattrs[:cattr.start()] + ' class="%s"' % newcls + newattrs[cattr.end():]
        else:
            newattrs = ' class="%s"%s' % (add_class, newattrs)
        cnt["n"] += 1
        return open_ + newattrs + close
    html2 = pat.sub(repl, html)
    return html2, cnt["n"]

# ---------- 3. Apply each mapping (tag, exact inline style -> class) ----------
MAPPINGS = [
    # (tag, style_val, add_class, expected_count)
    ("button", "color:var(--err)", "c-err", 1),
    ("button", "margin-left:auto;padding:2px 10px;font-size:12px", "btn-refresh", 2),
    ("button", "height:30px", "btn-h30", 1),
    ("div", "font-size:12px;color:var(--dim)", "subhead", 1),
    ("div", "font-size:12px;color:var(--dim);margin-top:6px", "subhead mt6", 2),
    ("div", "font-size:12px;color:var(--dim);margin-top:8px", "subhead mt8", 1),
    ("div", "align-items:stretch", "opsrow--stretch", 1),
    ("div", "flex:1;max-height:none", "opsbox--fill", 2),
    ("div", "margin-top:6px;font-size:12px", "mt6 fs-12", 2),   # .hint divs
    ("div", "max-width:70px", "w70", 1),
    ("div", "max-width:90px", "w90", 1),
    ("input", "height:32px;padding:2px", "input-bar", 1),
    ("input", "width:auto", "input-auto", 5),
    ("label", "margin-bottom:6px", "mb6", 1),
    ("label", "margin-top:6px", "mt6", 1),
    ("label", "margin-bottom:4px", "mb4", 2),
]
total = 0
for tag, sval, addc, expect in MAPPINGS:
    txt, n = strip_style(txt, tag, sval, addc)
    total += n
    flag = "OK" if n == expect else "!! expected %d" % expect
    log.append("%-6s %-55s -> +'%-16s'  hit=%d  %s" % (tag, sval[:54], addc, n, flag))

# ---------- 4. #netFields: class-based hide + JS toggle update ----------
net_before = txt.count('<div id="netFields" style="display:none;margin-bottom:8px">')
txt = txt.replace('<div id="netFields" style="display:none;margin-bottom:8px">',
                  '<div id="netFields" class="hidden mb8">')
log.append("#netFields inline->class  replaced=%d" % net_before)

js_old = '$("netFields").style.display=net?"":"none";'
js_new = '$("netFields").classList.toggle("hidden",!net);'
njs = txt.count(js_old)
txt = txt.replace(js_old, js_new)
log.append("#netFields JS style.display->classList.toggle  replaced=%d" % njs)

# ---------- 5. Verify + write ----------
remaining_static = len(re.findall(r'<[a-zA-Z][\w-]*\b[^>]*?\bstyle\s*=\s*"[^"]*"', txt))
# subtract runtime-injected (inside <script> string templates)
runtime = 0
for m in re.finditer(r'<[a-zA-Z][\w-]*\b[^>]*?\bstyle\s*=\s*"[^"]*"', txt):
    pre = txt[:m.start()]
    if (pre.count("<script") - pre.count("</script>")) > 0:
        runtime += 1
static_left = remaining_static - runtime

new_bytes = len(txt.encode("utf-8"))
h = hashlib.md5(txt.encode("utf-8")).hexdigest()[:10]
log.append("")
log.append("removed static inline styles this run: %d (target 26)" % total)
log.append("style= attrs remaining: total=%d runtime(script)=%d STATIC_LEFT=%d" % (remaining_static, runtime, static_left))
log.append("size bytes: %d -> %d ; md5 %s" % (orig_bytes, new_bytes, h))

# structural sanity
for tag in ["script", "style"]:
    o = txt.count("<" + tag); c = txt.count("</" + tag + ">")
    log.append("balance <%-5s>: open=%d close=%d %s" % (tag, o, c, "OK" if o == c else "!! MISMATCH"))
log.append("themeToggle present: %s ; --r-sm present: %s ; 0 raw 8px radius: %s" % (
    "themeToggle" in txt, "--r-sm" in txt, len(re.findall(r'border-radius:\s*8px', txt)) == 0))

ok = (static_left <= 1) and njs == 2 and net_before == 1 and all(
    x.count("!!") < 1 for x in log)
if ok:
    open(PATH, "w", encoding="utf-8", newline="").write(txt)
    print("WROTE", PATH)
else:
    print("ABORT (not writing) - review log below")
print(chr(10).join(log))
