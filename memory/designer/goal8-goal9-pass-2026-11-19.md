# Designer pass 2026-11-19 (auto-loop) — Goal #8 residual glyphs + Goal #9 tour module

parent: memory/goals/designer.md | sibling evidence: goal8-corejs-glyph-pass-2026-11-19.md
rule: memory/portal/file-modularity.md

## What ran this pass (verified, file changes)

### 1. Goal #8 Icon System — finished residual glyphs in NON-pinned files
Live sweep of index.html / ui/core.js / ui/uploads.js / ui/icons.js for emoji+dingbat:
- index.html: **0** dingbat (already [data-icon] spans; pin advanced 2026-11-19 per PIN_FILES comment).
- core.js: was 3 dingbat -> now **0**. Edits:
  - L467 DM summary `private → @Name` -> `private · @Name` (prose arrow removed; lock icon via st() kept).
  - L632 merge-queue button `↩ restore` -> `UI.icSVG("reset",13)+" restore"` (real icon case -> SVG).
  - L655 prune result `...item(s) → TODO_completed.md` -> `...item(s) to TODO_completed.md` (prose arrow removed).
- uploads.js: was 2 dingbat -> now **1** (see exclusion below). Edit:
  - L326 code comment `+ ↻ only (no polling)` -> `+ refresh-only (no polling)`.
- Balance check core.js: {} 278/278, () 1003/1003; [] 125/126 explained by pre-existing regex literal L455 `/\[DM\b...\]/gi` (escaped brackets) - NOT a syntax error. uploads.js fully balanced.

**Deliberate exclusion (documented, out of scope for #8):** uploads.js L231 `$("f_emoji").value=a?.emoji||"🤖"` is a *user-data default* for the per-agent avatar emoji field (stored content, not a UI icon). Replacing it with SVG would break the feature. So "no emoji remain" holds for all *icon-position* glyphs; the single remaining dingbat is user content.

=> Goal #8 acceptance (9+ icons in ui/icons.js [21 defined]; consistent use across panels; no icon-position emoji) is satisfied. Ledger already counts #8 reached (designer 8/10); this pass closes the residual gap.

### 2. Goal #9 Onboarding Tour — concrete first step: tour module + CSS built
- **ui/tour.js** (NEW, 96 lines, self-contained IIFE, no external deps, header pointer per modularity rule):
  - 4 steps in order: Fleet tab (#fleetBtn) -> Goals panel (#goalsBtn) -> Ops tab (#opsBtn) -> Uploads (#filesBtn).
  - First-visit gate via localStorage flag `portal.tour.v1`; auto-runs ~600ms after load if unset.
  - Coach-mark card (step counter + title + desc) positioned next to target with viewport clamp + flip-above; dimmed scrim; target raised above scrim as a spotlight (.tour-target outline).
  - Dismissible (Skip tour) + per-step Next/Finish; Finish/Skip set the flag so it never reappears. Missing-element step auto-skips.
  - Public `window.runTour()` for manual trigger / testing.
  - Verified: braces/parens/brackets all balanced (21/21, 80/80, 3/3); no stray identifiers.
- **ui/app.css** (appended `.tour-*` block): scrim/card/step/title/desc/bar/skip/target, ALL values via var(--token) — 0 hard-coded color/px (respects Goal #1 token rule).

## Remaining step for FULL #9 closure (ONE distinct operation, next pass)
- Add `<script src="ui/tour.js"></script>` to index.html (after ui/icons.js). index.html is PINNED -> requires pin advance: copy new index.html to `memory/designer/index_html_CANONICAL_<sha12>_2026-11-19x.html`, update PIN_FILES in memory_mirror.py to the new sha12 + backup path, commit.
- Then verify end-to-end: fresh profile (no flag) shows tour on load; 4 steps highlight correct targets; Skip/Finish sets flag; hard-refresh does not re-show. (Acceptance test per designer.md goal #9.)

NOTE: NOT recorded as reached in the ledger this pass — #9 is PROGRESS, not acceptance-passed (end-to-end wiring pending).
