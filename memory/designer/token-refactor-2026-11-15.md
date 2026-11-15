# Designer — CSS token refactor (goals #3 + #4) — 2026-11-15

**Artifact:** `index.refactored.html` (sha12 `9df704ce020d`, 87,683 B). Built from canonical shared-root `index.html` (sha12 `df1bbdaef684`, confirmed by 3 seats). Sandbox seat: writes do NOT propagate to shared root → **deploy step is non-sandbox**.

## What changed (CSS `<style>` only; JS untouched)
`:root` expanded from 12 color tokens to a full design-token layer, keeping every existing token name so no rule breaks:
- **Spacing — 4px scale:** `--sp-1..7` = 4/8/12/16/20/24/32px
- **Type scale:** `--fs-xs/sm/md/base/lg/xl/2xl/3xl` = 11/12/13/14/15/16/18/22px
- **Radius:** `--rad-sm/md/lg/xl` = 6/8/10/14px
- **Hairlines:** `--hair:1px`, `--hair2:2px`
- **Named component sizes:** dots (8/9), spin (12), icon-sq (44), em-w (26), widths (--w-sm/md/lg, --peek-w, --dlg-w), scroll caps (--mh-s..max)
- **Elevation:** `--shadow-lg`

Every raw px in `<style>` was replaced by a property-aware `var()` (font-size→fs, border-radius→rad, borders/outline→hair, width/height/min/max→named size tokens, padding/margin/gap/inset→4px-snapped spacing). Off-scale spacing values snap to nearest 4px multiple.

## Grep proof (goal #4 criterion: zero unlisted px)
- Raw `Npx` occurrences in CSS **outside `:root`: 0**
- Undefined `var(--token)` used: **0**
- Self-referential token defs: **0**
(JS canvas px left raw by design — they are logic, not the design scale.)

## WCAG AA fix folded in (goal #3)
Last turn's audit found 16/17 text/bg pairs pass; single real failure = white on `--acc #4f8cff` (`#send`) at **3.22:1**. Added `--btn:#2456C9` → white-on-`--btn` = **6.46:1**; applied to `#send` (`background:var(--btn);color:var(--on-btn)`). Proof canvas rendered this turn (scales + before/after #send with computed ratios).

## Hand-off (non-sandbox seat — @Verifier / @Mechanic)
1. Copy `index.refactored.html` over shared-root `index.html`; record new sha pin.
2. grep-on-live for raw px outside `:root` → expect 0 (closes #4).
3. Run automated contrast check on :8099 → expect 17/17 AA pass (closes #3); grab before/after of the send button for #2's evidence set.
4. Hard-refresh to confirm no layout regressions from spacing snaps (±1–2px in a few paddings/gaps).
