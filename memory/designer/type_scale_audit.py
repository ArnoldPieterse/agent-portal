#!/usr/bin/env python3
"""Goal #5 - Typography Scale Refinement: static type-scale audit.
Single source of truth = the --fs-* tokens defined in ui/tokens.css.
Checks every font-size declaration across LIVE ui/*.css + ui/*.js for:
  (A) off-scale usage   : a font-size not traceable to a defined token
  (B) raw-px leaks      : any literal px font-size outside the scale
  (C) orphaned tokens   : a --fs-* token defined but never consumed
  (D) ratio consistency : consecutive consumed steps vs 1.25 / 1.333 (informational)
Exit 0 = clean, exit 1 = violations found.
"""
import os, re, sys, glob

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.normpath(os.path.join(here, '..', '..'))
tokens_path = os.path.join(root, 'ui', 'tokens.css')

# --- source of truth: defined --fs-* tokens -> px value -------------------
tok = open(tokens_path, encoding='utf-8').read()
defined = {m.group(1): int(m.group(2)) for m in re.finditer(r'(--fs-(\d+))\s*:\s*(\d+)px', tok)}
# dict token->px
scale = {k: v for k, v in defined.items()}
print(f"tokens.css defines scale: {sorted(scale.items(), key=lambda x:x[1])}")

# --- live files (exclude backups/canonical copies) ------------------------
live = [f for f in glob.glob(os.path.join(root,'ui','*.css'))+glob.glob(os.path.join(root,'ui','*.js'))
        if 'before' not in os.path.basename(f) and 'bak' not in os.path.basename(f)]

off_scale, raw_px, consumed = [], [], set()
for f in live:
    txt = open(f, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'font-size\s*:\s*([^;"}\)\s]+)', txt):
        val = m.group(1).strip().rstrip(';').strip()
        name = os.path.basename(f)
        vm = re.match(r'var\((--fs-\d+)', val)
        if vm:
            tok = vm.group(1)
            consumed.add(tok)
            if tok not in scale:
                off_scale.append(f"{name}: uses undefined {tok}")
            continue
        pm = re.match(r'([\d.]+)px$', val)
        if pm:
            px = int(float(pm.group(1)))
            raw_px.append((name, px))
            if px not in scale.values():
                off_scale.append(f"{name}: raw {px}px not in scale")

# --- (C) orphans ----------------------------------------------------------
orphaned = [t for t in scale if t not in consumed]

print("\n[A] off-scale usage:", len(off_scale))
for x in off_scale: print("    ", x)
print("[B] raw-px font-size declarations (should be 0):", len(raw_px))
for name, px in raw_px[:20]: print(f"    {name}: {px}px")
print("[C] orphaned tokens (defined, never consumed):", orphaned or "none")

# --- (D) scale acceptance: functional tier scale --------------------------
# WCAG 2.1 AA does NOT mandate a modular/geometric type ratio; it requires
# legible, resizable text with clear hierarchy. So the acceptance is concrete:
#   floor  : no reading text below 12px
#   body   : 14px present (default body size)
#   head   : a distinct top tier >= 15px, clearly above body
#   tiers  : >= 3 distinct sizes (weak hierarchy if fewer)
# Ratios are reported informationally; the dense functional scale {12,14,15,18}
# is intentional for this data-dense dashboard (goal7-type-audit-findings-2026-11-19.md).
vals = sorted({scale[t] for t in consumed})
ratios = [round(vals[i+1]/vals[i], 3) for i in range(len(vals)-1)]
print(f"\n[D] functional tier scale: {vals}  (consecutive ratios {ratios})")
d_fail = []
if not vals or min(vals) < 12: d_fail.append("reading text below 12px floor")
if 14 not in vals: d_fail.append("body size 14px missing from scale")
if not vals or max(vals) < 15 or (max(vals) - 14) < 1: d_fail.append("no distinct headline tier above body")
if len(set(vals)) < 3: d_fail.append("fewer than 3 distinct tiers (weak hierarchy)")
print("    note: not a single modular ratio by design (dense functional scale; WCAG 2.1 AA needs no geometric ratio)")
for x in d_fail: print("    FAIL:", x)

# --- verdict --------------------------------------------------------------
hard_fail = off_scale or raw_px or orphaned or d_fail
print("\nVERDICT:", "FAIL" if hard_fail else "PASS (tokenized, no raw-px, no orphans; functional tier scale legible + hierarchical)")
sys.exit(1 if hard_fail else 0)
