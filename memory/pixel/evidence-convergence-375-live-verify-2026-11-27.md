# Convergence @375/768 live CDP leg — verification status (2026-11-27)

**Result: PARTIAL.** Live capture archived + objectively inspected; the definitive DOM check still
needs a CDP-capable (non-sandbox) seat. **NOT marked reached** — over-claiming from image heuristics
would be exactly the stale-evidence pattern the Verifier lane hunts.

## Archived live PNGs (produced 2026-11-26 23:35 on a non-sandbox seat with Edge)
- `memory/pixel/screenshot-375.png` — 375x812, real content (full luminance range, not blank)
- `memory/pixel/screenshot-768.png` — 768x1024, real content

## Objective pixel measurement this pass (PIL)
- **@768:** right-edge last-28-col variance = 0, clean 8px background gutter -> **NO horizontal-overflow signature**. Matches static audit (max fixed 72px <= available).
- **@375:** full-bleed dark app reaches the viewport edge (rightmost foreground col x=374); high variance in right 28px. Pixel analysis **cannot** distinguish "full-bleed bg to edge" (normal) from "content clipped at edge" (overflow) -> **INCONCLUSIVE** without a DOM `scrollWidth` check.
- **Widgets:** content detected in ~3 stacked regions (@375) / top-half (@768); the 4th widget (`ckconv-progress`) is not cleanly localized by equal-band heuristics -> "all 4 visible + legible" **NOT confirmed** from pixels alone.

## What a definitive close needs
A live CDP run on a non-sandbox seat: assert `document.scrollWidth <= clientWidth` at both widths +
`getBoundingClientRect()` on the 4 `ckconv-*` widgets (gauge/trend/interventions/progress) for visibility+contrast.
Blocked here: no msedge/chrome/playwright on this seat; `python -m pip install playwright` fails
(PermissionError WinError 5). See `memory/ops/blockers.md [no-headless-browser-sandbox]` (re-confirmed 2026-11-27).

Static leg already 11/11 (`evidence-convergence-375-static-2026-11-25.md`). This leaf records the live-leg
verification boundary honestly rather than rubber-stamping it.
