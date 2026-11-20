#!/usr/bin/env python3
# Generates memory/designer/icons_gallery.html from the live ui/icons.js set.
import re, html
src = open("ui/icons.js", encoding="utf-8").read()
icons = dict(re.findall(r"^\s*([a-z0-9_]+):\s*'(<svg.*</svg>)'\s*,?$", src, re.M))
def norm(n): return n.replace("-", "_")
def sized(name, sz):
    ins = '<svg width="%d" height="%d" ' % (sz, sz)
    return icons[norm(name)].replace('<svg ', ins, 1)
allnames = list(icons.keys())
cells = "".join(
    '<div class="cell" title="%s">%s</div><div class="lbl">%s</div>' % (n, sized(n, 24), n)
    for n in allnames)
def strip(n):
    return "".join('<span class="cell" title="%s @%dpx">%s</span>' % (n, s, sized(n, s)) for s in (16, 24, 32))
sc = "".join('<div class="srow"><span class="snm">%s</span>%s</div>' % (n, strip(n)) for n in
             ["agent", "settings", "warning", "chevron-down", "clock", "external"])
tpl = ("<!doctype html><html><head><meta charset=utf-8>"
"<meta name=viewport content='width=device-width,initial-scale=1'>"
"<title>Portal Icon Set</title><style>"
":root{--bg:#0f1115;--panel:#171a21;--fg:#e6e8ec;--mut:#8b93a1;--line:#262b34;--acc:#5b9dff}"
"*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);"
"font:14px/1.5 -apple-system,'Segoe UI',Roboto,sans-serif;padding:24px}"
"h1{font-size:18px;margin:0 0 4px}p.sub{color:var(--mut);margin:0 0 20px;font-size:13px;max-width:70ch}"
".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(72px,1fr));gap:8px}"
".cell{background:var(--panel);border:1px solid var(--line);border-radius:8px;height:46px;"
"display:flex;align-items:center;justify-content:center;color:var(--fg)}"
".lbl{font:10px/1 ui-monospace,Consolas,monospace;color:var(--mut);text-align:center;margin-top:5px}"
"h2{font-size:14px;margin:26px 0 10px;color:var(--fg)}"
".srow{display:flex;align-items:center;gap:14px;padding:8px 0;border-bottom:1px solid var(--line)}"
".snm{font:11px ui-monospace,Consolas,monospace;color:var(--mut);width:96px}"
".srow .cell{background:none;border:none;height:auto;width:auto}"
"</style></head><body>"
"<h1>Portal Icon Set <span style='color:var(--acc)'>\u00b7 @@COUNT@@ glyphs</span></h1>"
"<p class=sub>ui/icons.js \u2014 24\u00d724 viewBox, 1.5px stroke, currentColor (Feather/Lucide grid). "
"Grid below at 24px; scaling strip at 16/24/32px. No external icon library.</p>"
"<div class=grid>@@CELLS@@</div><h2>Scaling \u2014 16 / 24 / 32px</h2>@@SCALE@@"
"</body></html>")
tpl = tpl.replace("@@COUNT@@", str(len(allnames))).replace("@@CELLS@@", cells).replace("@@SCALE@@", sc)
out = "memory/designer/icons_gallery.html"
open(out, "w", encoding="utf-8").write(tpl)
print("gallery written: %d icons -> %s (%d bytes)" % (len(allnames), out, len(tpl)))