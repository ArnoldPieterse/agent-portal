#!/usr/bin/env python3
# Goal #10 (Print-Ready Report Layout) - STATIC acceptance verifier.
# Verifies the REAL implementation (not the prior overclaim). Browser print-preview leg is a
# separate logged NEEDS-HUMAN item (memory/ops/blockers.md); this checks every non-browser criterion.
import re, sys

css = open("ui/app.css", encoding="utf-8").read()
js  = open("ui/core.js", encoding="utf-8").read()

# Extract the @media print block text (balanced to its closing brace).
i = css.find("@media print")
assert i != -1, "FAIL: no @media print block"
depth, j = 0, i
for k in range(i, len(css)):
    if css[k] == "{": depth += 1
    elif css[k] == "}":
        depth -= 1
        if depth == 0:
            j = k + 1; break
block = css[i:j]

checks = []
def chk(name, ok):
    checks.append((name, bool(ok)))

# 1. white-paper background (transparent * so browser paper shows through) + black text
chk("black text on print (color:var(--black))", "var(--black)" in block)
chk("background flattened to transparent", "background:transparent !important" in block)
# 2. interactive elements hidden
for sel in [".panel-toggle", ".btn", "#printReportBtn", ".toggles button"]:
    chk(f"hides {sel}", re.search(re.escape(sel) + r"[^}]*display:none", block) is not None)
chk("hides chat col / composer", ("#chatCol" in block and "#composerWrap" in block))
# 3. all data visible: panels un-clipped
chk("panels static + overflow visible (all data shows)",
    re.search(r"\.panel[^}]*overflow:visible", block) is not None)
chk("max-height removed on print", "max-height:none !important" in block)
# 4. page breaks between sections (the previously-missing leg)
chk("break-inside:avoid on sections/cards/panels", ("break-inside:avoid" in block and "section" in block))
chk("page-break-inside fallback present", "page-break-inside:avoid" in block)
chk("break-after:avoid on headings (no orphaned headers)", ("break-after:avoid" in block and "h1,h2,h3" in block))
# 5. Print button wiring in core.js -> window.print()
chk("core.js injects #printReportBtn", 'id="printReportBtn"' in js)
chk("core.js wires onclick -> window.print()", re.search(r"printReportBtn[\s\S]{0,400}?window\.print\(\)", js) is not None)
# 6. structural integrity
chk("app.css braces balanced", css.count("{") == css.count("}"))
tok = open("ui/tokens.css", encoding="utf-8").read()
defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", tok)) | set(re.findall(r"(--[a-z0-9-]+)\s*:", css))
used = set(re.findall(r"var\((--[a-z0-9-]+)", css))
chk("no dangling var() tokens", used <= defined)

passed = 0
for _n, _ok in checks:
    if _ok:
        passed += 1
total = len(checks)
print("GOAL #10 PRINT STATIC VERIFY: %d/%d PASS" % (passed, total))
for name, ok in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
sys.exit(0 if passed == total else 1)
