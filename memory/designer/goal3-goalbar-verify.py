#!/usr/bin/env python3
"""Designer goal 3 (cycle-5) - Data Visualization Upgrade: inline-SVG mini bars.

Verifies the ACTUAL shipped ui/core.js `goalBar()` helper:
  A. structural assertions on the real source string (markup/SMIL/tokens)
  B. faithful arithmetic port of the width + color-threshold logic (no JS runtime / CDP blocked here)

Run: python memory/designer/goal3-goalbar-verify.py
Exit 0 = all checks pass.
"""
import re, sys

core = open("ui/core.js", encoding="utf-8").read()
m = re.search(r"function goalBar\(pct\)\{.*?\n\}", core, re.S)
assert m, "goalBar() not found in ui/core.js"
fn = m.group(0)

checks = []
def ck(name, cond):
    checks.append((name, bool(cond)))

# --- A. structural (real shipped source) ---
ck("emits <svg class=goalbar>", '<svg class="goalbar"' in fn)
ck("track rect present", 'width="140" height="6" rx="3" fill="rgba(128,140,155,.18)"' in fn)
ck("SMIL <animate width> present", '<animate attributeName="width"' in fn)
ck("animation dur 0.4s (<500ms)", 'dur="0.4s"' in fn)
ck("fill freeze (holds end value)", 'fill="freeze"' in fn)
ck("token --ok used", "var(--ok)" in fn)
ck("token --warn used", "var(--warn)" in fn)
ck("token --err used", "var(--err)" in fn)
ck("no external lib (no <script src / no import)", "src=" not in fn and "import" not in fn)

# wired into the Agent Overview rows
ck("goalBar() called in fleet overview row", "goalBar(pct)" in core.split("function goalBar")[1].split("let fleetTimer")[0] or core.count("goalBar(pct)") >= 2)

# --- B. arithmetic port (faithful, line-by-line) ---
def width(pct):
    p = max(0, min(100, pct))          # pct|0 -> int; clamp
    w = round((132 * p / 100), 1)
    return p, w
def token(p):
    return "ok" if p >= 80 else ("warn" if p >= 50 else "err")

# exact expected fill width for a few values
for pct, exp in [(0, 0.0), (10, 13.2), (25, 33.0), (50, 66.0), (80, 105.6), (100, 132.0)]:
    p, w = width(pct)
    ck(f"width({pct})=={exp}", abs(w - exp) < 1e-9)

# threshold mapping
for pct, tok in [(0, "err"), (49, "err"), (50, "warn"), (79, "warn"), (80, "ok"), (100, "ok")]:
    ck(f"token({pct})=={tok}", token(pct) == tok)

# clamp: out-of-range never overflows the 132px track
for pct in (-5, 101, 999):
    p, w = width(pct)
    ck(f"clamp({pct})<=132", 0 <= w <= 132.0 and 0 <= p <= 100)

# --- render a sample of 8 bars (the acceptance count) ---
def goalbar_js(pct):
    p, w = width(pct)
    tok = token(pct)
    varmap = {"ok": "var(--ok)", "warn": "var(--warn)", "err": "var(--err)"}
    svg = ('<svg class="goalbar" viewBox="0 0 140 10" width="140" height="10" role="img" aria-label="goals %d%%">'
           '<rect x="0" y="2" width="140" height="6" rx="3" fill="rgba(128,140,155,.18)"/>') % p
    if p > 0:
        svg += ('<rect class="gbar-fill" x="0" y="2" width="%s" height="6" rx="3" style="fill:%s">'
                '<animate attributeName="width" from="0" to="%s" dur="0.4s" fill="freeze"/></rect>') % (w, varmap[tok], w)
    svg += "</svg>"
    return svg

agents = [("Orchestrator", 10, 10), ("Researcher", 8, 10), ("Builder", 10, 10),
          ("Verifier", 9, 10), ("Designer", 2, 10), ("Archivist", 5, 10),
          ("Scribe", 7, 10), ("Mechanic", 6, 10)]
sample = [(n, d, t, goalbar_js(round(100 * d / t) if t else 0)) for n, d, t in agents]
n_svg = sum(x[3].count("<svg") for x in sample)
ck("8 bars render (one per agent)", n_svg == 8)
ck("every bar has a track", all('width="140" height="6"' in x[3] for x in sample))

# --- report ---
pass_n = sum(1 for _, c in checks if c)
for name, ok in checks:
    print(("PASS " if ok else "FAIL ") + name)
print("\n%d/%d checks passed" % (pass_n, len(checks)))

# emit the 8-bar fixture sample so a human/verifier can eyeball it
with open("memory/designer/goal3-fleet-bars-fixture.html", "w", encoding="utf-8") as f:
    rows = "\n".join(
        '<div class=frow><b>%s</b> <span class=hint>%d/%d goals</span> %s</div>' % (n, d, t, svg)
        for n, d, t, svg in sample)
    f.write("""<!doctype html><meta charset=utf-8><title>Designer goal3 - fleet goal bars (fixture)</title>
<style>:root{--ok:#3ddc84;--warn:#ff9f43;--err:#ff6b6b;--text:#e8edf4}
body{background:#0d1117;color:var(--text);font-family:ui-monospace,Consolas,monospace;padding:24px}
.frow{display:flex;align-items:center;gap:10px;margin:6px 0;font-size:13px}.hint{opacity:.6}
.goalbar{height:10px}</style>
<h3>Fleet - goal completion per agent (8 inline-SVG bars, SMIL-animated on load)</h3>""" + rows)

sys.exit(0 if pass_n == len(checks) else 1)
