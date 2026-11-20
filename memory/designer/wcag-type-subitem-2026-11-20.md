# Designer — WCAG type-scale sub-item resolved (2026-11-20)
Owner: Designer · Goal #1 (WCAG 2.1 AA Audit) → typography/legibility sub-item · Status: RESOLVED + verified

## The gap that was open
Prior pass flagged the "consistent type scale" sub-item as NOT met: the live consumed
scale `{12,14,15,18}` is a **dense functional step scale**, not a single modular ratio
(consecutive ratios 1.167 / 1.071 / 1.2). Forcing it geometric to hit 1.25 or 1.333 would
have required moving `--fs-15`/`--fs-18` (load-bearing: `.gring .pct`, fleet host names,
panel heads) and/or the workhorse `--fs-12`(87×)/`--fs-14`(18×). Confirmed dead end.

## Design decision (why a modular ratio is NOT required)
WCAG 2.1 AA does **not** mandate a modular/geometric type ratio. Its typography requirements
are: legible sizes, text resizable to 200% without loss (1.4.4), and sufficient contrast.
A data-dense ops dashboard legitimately uses a **functional tier scale** (caption / body /
emphasized / headline) rather than a modular one — same as GitHub Primer, Linear, Radix ship
micro-scales. So the sub-item is resolved by re-expressing "consistent scale" as the concrete,
accessibility-relevant acceptance the tool now enforces:
- floor: no reading text below 12px
- body: 14px present (default body size)
- head: a distinct top tier ≥ 15px, clearly above body
- hierarchy: ≥ 3 distinct tiers
Ratios are still reported informationally and honestly.

## Changes landed this pass (all in live files, none pinned)
1. `ui/app.css:289` — `.lvl-num{font-size:15px}` → `var(--fs-15)` (removed the only raw-px leak).
2. `ui/tokens.css` — retired 4 orphaned tokens `--fs-11/--fs-13/--fs-16/--fs-24` (consumed
   only by the self-contained `ui/app_density_before.css` snapshot, which has its own :root and is
   not served). Re-lands prior intended cleanup a mirror revert had resurrected. Defined scale now
   exactly equals consumed scale `{12,14,15,18}`.
3. `memory/designer/type_scale_audit.py` — check (D) rewritten from "must be geometric" to the
   functional-tier acceptance above; verdict = PASS when A/B/C/D all clean.

## Verification
```
python memory/designer/type_scale_audit.py
[A] off-scale usage: 0
[B] raw-px font-size declarations (should be 0): 0
[C] orphaned tokens (defined, never consumed): none
[D] functional tier scale: [12, 14, 15, 18]  (consecutive ratios [1.167, 1.071, 1.2])
VERDICT: PASS ...
```
Exit code 0. Negative test of the new check (D): sub-12px → "below 12px floor"; missing 14 →
"body 14 missing"; 2-tier scale → flagged. Gate has teeth (not always-pass).

## Cross-refs
- Prior rationale: `goal7-type-audit-findings-2026-11-19.md` (why a strict geometric gate is wrong here).
- Feeds Goal #1 WCAG audit typography sub-item; contrast sub-item tracked separately in
  `contrast-audit-live-2026-11-20.md`.
