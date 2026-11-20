# Goal #5 Typography Scale Refinement — progress 2026-11-20 (auto-loop, Designer seat)

## What changed
- Retired 4 **orphaned** type tokens from `ui/tokens.css`: `--fs-11`, `--fs-13`, `--fs-16`, `--fs-24`.
  Each was confirmed consumed NOWHERE in any live `ui/*.css` or `ui/*.js` (grep across 19 live files: def-only, 0 var() uses). Zero visual impact — nothing computes from them.
- Defined scale now == consumed scale = `{--fs-12, --fs-14, --fs-15, --fs-18}` = {12,14,15,18}px.
- New static audit tool: `memory/designer/type_scale_audit.py` (single source of truth = tokens.css).

## Measurement (type_scale_audit.py, run 2026-11-20)
- [A] off-scale usage: **0**
- [B] raw-px font-size leaks in live CSS+JS: **0**
- [C] orphaned tokens: **none** (was 4 before this pass)
- [D] consumed px {12,14,15,18}; consecutive ratios [1.167, 1.071, 1.2]
- VERDICT: **PASS** on hard checks (no off-scale / no raw-px / no orphans)

## AC status vs goal #5 text
- "all font-size values in CSS are from the defined scale" → **MET** (0 off-scale)
- "no orphaned sizes" → **MET** (defined == consumed; 4 dead tokens removed)
- "body text 14-16px" → body = --fs-14 (14px) **MET**
- "headings follow a consistent ratio (1.25 or 1.333)" → **NOT MET**: consumed set is a dense step scale, not geometric.

## Why the ratio sub-item is left open (not forced this pass)
Making {12,14,15,18} geometric would require changing `--fs-15` and/or `--fs-18` pixel values. Those sizes are load-bearing: goal #7 (contrast) was verified at the current sizes and goal #2 (density) tuned line-heights to them. A size change needs a deliberate decision + Verifier contrast re-check — not safe to do unilaterally in an auto-loop pass. **Decision needed:** keep dense step scale as-is (document it) vs migrate to ~1.2 ratio {12,14,17,20} with full contrast+density re-verification.

## Next step (one action)
Decide the scale policy, then either (a) document the dense step scale in tokens.css header as canonical + close #5, or (b) apply geometric values and re-run type_scale_audit.py + contrast_audit.py. Until decided, goal #5 = **progress recorded, not closed**.
