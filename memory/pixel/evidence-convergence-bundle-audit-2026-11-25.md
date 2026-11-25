# Convergence Bundle-Size + Dead-Code Audit (Pixel)
Date: 2026-11-25 · Goal #8.

**Footprint: 25.4 KB / budget 30 KB (WITHIN, headroom 4.6 KB)** · **Dead symbols: 0** · **File well-formed: yes**

## Measurement (ui/cockpit-convergence.js)
- Total module: **26010 bytes = 25.4 KB**
- CSS blob (rendered): 4.9 KB · JS logic + lineage data: 20.5 KB
- Baseline pre-this-pass was 22.5 KB; +2.9 KB is the goal #6 print CSS + goal #7 persistence feature (legit features, not bloat).

## Dead-code scan (grep, reference-based)
- All 34 top-level functions referenced >=1x (calls AND event-handler callbacks, e.g. trapFocus -> keydown add/removeEventListener).
- **0 dead symbols.** Designer cycle-17 build had no leftover dead helpers from prior widget iterations to tree-shake.

## Stated KB budget
- Budget for the whole convergence module (JS + inline CSS): **30 KB**. Current 25.4 KB -> within, ~4.6 KB headroom.
- Audit diff is net-zero on code (nothing removable without regression); criterion met via the 'under budget' branch.

## No behavioral regression in the 4 widgets
- Widget render logic untouched this pass; only additive, guarded changes (print CSS block, .ckconv-since chip, persistence).
- Full-file structure verified well-formed: balanced braces/parens/brackets after masking the two regex literals (the char-class replace and the \D digit-strip); IIFE init path intact.
- Live browser load-test is the one residual step (sandbox has no browser - recorded once in memory/ops/blockers.md); static well-formedness + intact init path substitute for it.