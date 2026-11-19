#!/usr/bin/env python3
# Goal #2 (Information Density Pass) - STATIC measurement of the density-tokenization surface.
# NOTE: this measures the NON-browser leg only. The acceptance criterion "reduce vertical whitespace by 20%
# (before/after screenshots, no overlap/clipping)" requires a live render = logged NEEDS-HUMAN CDP item
# (memory/ops/blockers.md). Do NOT treat this script's PASS as screenshot-level closure.
import re, sys

css = open("ui/app.css", encoding="utf-8").read()
tok = open("ui/tokens.css", encoding="utf-8").read()

# 1. All line-height values tokenized (0 hardcoded bare numbers in line-height decls)
lh_decls = re.findall(r"line-height\s*:\s*([^;}]+)", css)
hard_lh = [d for d in lh_decls if not re.search(r"var\(--lh-", d)]

# 2. padding/margin hardcoded px count (should be ~0; a few deliberate micro-values allowed)
px_padmar = re.findall(r"(?:padding|margin)[a-z-]*\s*:\s*([^;}]+)", css)
hard_px_pm = [d for d in px_padmar if re.search(r"\b\d+(?:\.\d+)?px", d) and "var(" not in d]
sp_refs = len(re.findall(r"var\(--sp-", css))
lh_refs = len(re.findall(r"var\(--lh-", css))

checks = []
def chk(name, ok, detail=""):
    checks.append((name, bool(ok), detail))

chk("line-height: 0 hardcoded (all var(--lh-*))", not hard_lh,
    "hardcoded=%s" % hard_lh if hard_lh else "%d decls all tokenized" % len(lh_decls))
chk("padding/margin: <=4 hardcoded px (deliberate micro-values only)", len(hard_px_pm) <= 4,
    "hardcoded_px=%d %s" % (len(hard_px_pm), hard_px_pm[:6]))
chk("spacing tokens applied (var(--sp-*) used broadly)", sp_refs >= 150, "count=%d" % sp_refs)
chk("line-height tokens applied (var(--lh-*) used broadly)", lh_refs >= 8, "count=%d" % lh_refs)
# token definitions present
define_lh = set(re.findall(r"(--lh-[a-z]+)\s*:", tok))
define_sp = set(re.findall(r"(--sp-\d+)\s*:", tok))
chk("line-height tokens defined (tight/caption/base/loose/mono)",
    {"--lh-tight","--lh-caption","--lh-base","--lh-loose","--lh-mono"} <= define_lh, "defined=%s" % sorted(define_lh))
chk("spacing scale defined (--sp-*)", len(define_sp) >= 6, "defined=%d tokens" % len(define_sp))

passed = sum(1 for _, ok, _ in checks if ok)
total = len(checks)
print("GOAL #2 DENSITY STATIC VERIFY: %d/%d PASS (static leg only; screenshots still need browser)" % (passed, total))
for name, ok, detail in checks:
    print("  [%s] %s  %s" % ("PASS" if ok else "FAIL", name, detail))
sys.exit(0 if passed == total else 1)
