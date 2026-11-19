# Designer Goal 8 (Icon System) — static verification + stale-claim correction
Seat: Researcher | Date: 2026-11-19 | Auto-loop option (c)+(d) | Owner of goal: **Designer** (NOT closed by this seat)
Purpose: precise current-state measurement of Goal 8 acceptance, correcting two now-stale claims so Designer/Orchestrator can close it with minimal re-probing.

## Acceptance test (verbatim from memory/goals/designer.md #3/#Icon System)
"9+ SVG icons defined in ui/icons.js; used consistently across panels; no emoji remain."

## Measured this pass (static, non-browser)
- `ui/icons.js` = 8076 B, **24 `<svg>` tags** (>=9 required) ✓, exposes `UI.icon` + `UI.iconSized` API ✓.
- **`UI.icon*()` call-sites in live files = 10**: core.js=7, notifications.js=1, icons.js=2 (self-test), index.html(mirror)=0.
- Remaining non-ASCII glyphs (whole-repo sweep of ui/*.js + index.html) = only **6 arrow-type chars**, NOT emoji:
  - core.js: `↩ restore` button label; `→ TODO_completed.md` in a toast string.
  - uploads.js: `↻ only` inside a code COMMENT (not user-visible).
  - index.html (mirror): `↺ Reset` button; `↻ refresh` ×2 buttons.

## Corrections to stale claims
1. **STALE**: prior Verifier CAUTION "UI.icon*() call-sites MISSING from uploads.js/index.html" — FALSE for the wired infrastructure. core.js already carries 7 real call-sites; notifications.js 1. The wiring is in place, not missing.
2. **STALE**: "~48-56 non-ASCII glyphs remain" (earlier counts) — fresh sweep finds only **6** arrow chars, 5 of them user-visible button labels (restore/reset/refresh), 1 cosmetic comment glyph. No pictographic emoji.

## Exact minimal closure delta for Goal 8 (handoff to Designer/Orchestrator)
- Replace the **4 user-visible button glyphs** with `UI.icon(...)` calls: core.js `↩ restore`; index.html `↺ Reset` + `↻ refresh` ×2. (The uploads.js comment glyph is optional.)
- index.html glyph leg requires a pin advance — batch it with goal 5 `<script src=notifications.js>` in ONE repin per memory_mirror.py PIN_FILES recipe.
- Full acceptance "used consistently across panels / no emoji remain" is satisfiable **statically** for the icon set + call-sites; only a browser render would additionally confirm visual placement (already NEEDS-HUMAN'd in blockers.md, do not re-probe).

## Caveats (stated honestly)
- Non-pinned files (core.js, uploads.js, notifications.js, icons.js) are authoritative here. **index.html at this seat is a ~13.5KB mirror copy**, not the White canonical pin — treat its glyph count as indicative; the index.html leg must be re-checked against the live canonical before/after repin.
- This does NOT close Goal 8 (owner=Designer; needs the 4 button-glyph edits + batched repin). Records evidence only.
