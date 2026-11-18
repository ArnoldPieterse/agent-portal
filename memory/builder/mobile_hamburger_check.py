#!/usr/bin/env python
# Builder goal #8 (Mobile Responsive Pass) - hamburger nav wiring check.
# No headless browser in this sandbox, so this verifies the DOM<->CSS<->JS contract
# that a 375px viewport render depends on: button present + wired + CSS collapse rules.
import sys, re

def read(p):
    return open(p, encoding="utf-8").read()

html = read("index.html")
css = read("ui/app.css")
js = read("ui/uploads.js")

checks = []
def ck(name, ok):
    checks.append((name, bool(ok)))

# --- DOM (index.html) ---
m = re.search(r'<button[^>]*id="navToggle"[^>]*>', html)
ck("DOM: #navToggle button exists", m)
ck("DOM: navToggle has aria-controls=toggles", m and 'aria-controls="toggles"' in m.group(0))
ck("DOM: navToggle has aria-expanded init", m and 'aria-expanded=' in m.group(0))
ck("DOM: #toggles span id present", re.search(r'<span[^>]*class="toggles"[^>]*id="toggles"', html) or re.search(r'id="toggles"[^>]*class="toggles"', html))

# --- CSS (ui/app.css) ---
ck("CSS: base .nav-toggle hidden on desktop", re.search(r'\.nav-toggle\{display:none\}', css))
# collect the body of EVERY max-width:480px media block (there are two; edits live in the second)
blk = "".join(re.findall(r'@media \(max-width:480px\)\{(.*?)\n\}', css, re.S))
ck("CSS: 480px .toggles collapsed by default (display:none)", re.search(r'\.toggles\{display:none\}', blk))
ck("CSS: 480px nav-open reveals .toggles", re.search(r'#modeBar\.nav-open \.toggles\{display:flex', blk))
ck("CSS: 480px .nav-toggle shown as button", re.search(r'\.nav-toggle\{display:inline-flex', blk))

# --- JS (ui/uploads.js) ---
ck("JS: reads #navToggle + #modeBar", 'navToggle' in js and 'modeBar' in js)
ck("JS: toggles nav-open class", '.classList.toggle("nav-open"' in js or "classList.toggle('nav-open'" in js)
ck("JS: updates aria-expanded", 'aria-expanded' in js)
ck("JS: closes on Escape", re.search(r'e\.key==="Escape"', js))
ck("JS: closes on outside click", re.search(r'bar\.contains\(e\.target\)', js))

# --- report ---
pass_n = sum(ok for _, ok in checks)
for name, ok in checks:
    print(("PASS " if ok else "FAIL ") + name)
print(f"\n{pass_n}/{len(checks)} wiring checks passed")
sys.exit(0 if pass_n == len(checks) else 1)
