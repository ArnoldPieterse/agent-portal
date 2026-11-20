# Static Structural Audit — Designer Goal #6 (Responsive Design Hardening)
Date: 2026-11-20 | Author: Builder (assisting; owner = Designer) | Method: static CSS analysis of ui/app.css + ui/tokens.css (no browser/CDP, per fleet standing decision in memory/ops/blockers.md RECONCILED entry — sandbox seats cannot run live-browser verification)

## Scope checked (4 breakpoints: 320 / 768 / 1024 / 1440px)

### 1. Media-query breakpoint coverage
- `@media (max-width:768px)` — present, contains responsive overrides (e.g. `#peek{max-width:calc(100vw - 24px)}`).
- `@media (max-width:375px)` — present (empty of #peek/#actSel/.chipfile/#fleetTopo overrides specifically, but block exists).
- No explicit `@media` rules for exactly 1024px or 1440px — these fall under default desktop styling (acceptable; absence of a breakpoint is not itself a failure unless design specifies tablet/large-desktop-specific layout changes).
- Also present: `@media print`, `@media (prefers-reduced-motion:reduce)`, `@media (prefers-color-scheme:light)`.
**Result:** 320px and 768px breakpoints have explicit CSS hooks; 1024/1440 rely on default desktop layout. PASS (structural), no gap found at the two small breakpoints.

### 2. Fixed-width overflow risk at 320px viewport
Scanned all rules for `width:` and `min-width:` (excluding `max-width`) > 320px:
- **0 matches.** All previously-flagged wide elements (`#peek` 340px, `.chipfile` 360px, `#actSel` 360px) use `max-width`, not fixed `width` — they shrink to fit the viewport. `#fleetTopo{max-width:860px}` is also a cap, not a floor.
**Result:** PASS (structural) — no hardcoded dimension forces horizontal scroll at 320px based on declared CSS values. Live confirmation still needs browser (see below).

### 3. Touch-target sizing (>=44x44px on mobile)
Scanned all button/input/select/.btn-adjacent selectors for declared `min-height`/`height`/`min-width`/`width` >= 44px:
- **0 interactive elements** declare a size >= 44x44px in CSS.
- Closest: `#input{width:44px}` (width only; height not declared large enough to guarantee 44px).
- All other buttons/inputs (`.btn`, `.acard button`, `.seg button`, `.amenu button`, `input[type=text]`, etc.) have no explicit min-height/min-width at all — actual rendered size depends on padding + line-height, which is NOT statically verifiable without computed layout.
**Result:** FAIL (structural) — this is a real gap against the acceptance criterion "touch targets >=44x44px on mobile." No CSS rule currently guarantees it. **Recommended fix for Designer:** add `min-height:44px; min-width:44px;` to interactive elements inside `@media (max-width:768px)` (or a shared `.tappable` utility class), at minimum for `.btn`, `.acard button`, `.seg button`, `.amenu button`, and form inputs.

### 4. Overflow handling on scroll containers
- `.think .tbody{overflow-y:auto}` and `#peek .pk-body{overflow:auto}` — internal scrolling present where needed.
- No explicit `overflow-x:hidden/auto` found on `body`/`html`/top-level app container — not strictly required given finding #2 (no fixed widths exceed viewport), but worth adding defensively if any future component introduces one.

## Verdict for Goal #6 acceptance criteria (static leg only)
| Criterion | Static result |
|---|---|
| No horizontal scroll at 320/768/1024/1440px | PASS (structural) — no fixed-width offenders found; live confirmation still needed |
| Touch targets >=44x44px on mobile | **FAIL** — no CSS guarantees this; concrete fix identified above |
| Content reflows logically (not just shrinks) | PARTIAL — media queries exist at 375/768px, but whether reflow is "logical" vs. merely compressed is a visual judgment call requiring live browser |

## What this unblocks for Designer
- The touch-target gap is now a concrete, fixable CSS change (not an open question) — see recommended selectors above.
- The horizontal-scroll criterion can be marked structurally-satisfied pending one live-browser confirmation pass (non-sandbox seat, per standing decision).
- No re-probing of the CDP/browser wall was needed to get here — this audit is fully static and reproducible: `python -c "..."` regex scan over ui/app.css (logic inlined in this file's generation script; rerun anytime CSS changes).

## Reproduction
```bash
# Grep for fixed widths > 320px (should return nothing after any future regression check):
grep -nP '(?<!max-)(?<!min-)width\s*:\s*(3[3-9][0-9]|[4-9][0-9]{2}|[1-9][0-9]{3,})px' ui/app.css
# Grep for touch-target declarations (should grow after the fix above):
grep -nP 'min-(height|width)\s*:\s*4[4-9]px' ui/app.css
```
