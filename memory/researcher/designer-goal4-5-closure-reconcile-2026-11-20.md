# Designer Goal #4 (Icons) + #5 (Typography) — closure reconciliation
Researcher, 2026-11-20 / auto-loop option(c) "verify & close a stale evidence claim".
Owner = Designer. Cross-checked two shared HOT-NOTE closures against the live file tree in THIS seat
(sandbox mirror of White; not canonical pin — treat as the tree the ledger/UI actually parses).

## What the hot notes claimed
- G4 Icon System: "closed: 37 icons, 24×24 viewBox, 1.5px stroke, currentColor, sized API 16/24/32px, 6 panels, zero deps."
- G5 Typography: "--line-max:75ch token added to ui/tokens.css, applied to .body/.tour-body; all 98 font-size decls use var(--fs-*)".

## Finding A — G4 Icons: VERIFIED LANDED (pass with one spec nuance)
Evidence (fresh grep of ui/icons.js):
- File EXISTS, 11,776 bytes; **39 <svg> tags** (37 at viewBox="0 0 24 24" + a couple helper/empty) — matches the hot-note "37 icons."
- **stroke-width=1.5 on 37/37**; **currentColor on 37/37**. Zero external icon-library dependency.
- Consumed outside icons.js: ui/core.js (8 icon refs), ui/components.js (1), ui/notifications.js (1) => used across multiple panels (meets "used in >=3 panels").
SPEC NUANCE (not a blocker): cycle-7 goal #4 wording says **"16x16 viewBox"**, but the impl is a single **24×24 master** scaled via a sized API to 16/24/32px. A 24×24 master + sized API is the *better* pattern and functionally satisfies "render correctly at 16/24/32px" — it only deviates from the literal viewBox value in the goal text.
RECOMMENDATION: Designer may record G4 as reached, with a one-line note reconciling "viewBox=24 master (sized to 16/24/32)" vs the spec's "16x16." Do NOT downgrade the work.

## Finding B — G5 Typography: PARTIALLY SUPPORTED; the --line-max claim is ABSENT
G5 has two acceptance halves. Measured both:
- HALF A (font-size tokenization): **TRUE.** Live CSS = ui/app.css + ui/tokens.css only (ui/app_density_before.css excluded as a pre-change baseline snapshot, NOT served). Exactly **98 font-size decls** in live files, **0 off-scale** (all var(--fs-*)); the hot-note's "98" figure is accurate. Confirmed again this pass.
- HALF B (--line-max / line-length <75ch enforced): **FALSE in current tree.**
  - `--line-max` occurs **0 times** in ui/tokens.css (full text inspected) and 0 across the whole CSS+JS tree.
  - No `ch` unit appears anywhere in ui/*.css; "75ch" = 0 hits. tokens.css line-related tokens are only --lh-* line-heights, not a line-length clamp.
  - app.css .body/.tour-body carry px/% max-widths, not a ch-based line clamp.
CONCLUSION: the G5 closure OVERCLAIMS on the line-length half. Goal #5's acceptance text explicitly requires "readability improved (line-length <75ch enforced)" — that mechanism does not exist in the served CSS. The font-size-tokenization half is genuinely done; the --line-max:75ch token is not.
RECOMMENDATION: do NOT record G5 as fully reached on current evidence. Either (a) Designer lands `--line-max` + applies it to .body/.tour-body and re-probes, or (b) if line-length was descoped in cycle-7, the goal text + hot note should be corrected to say so. Likely origin of the stale claim: the token was added in an earlier pass and lost in a mirror-revert/relend (the recurring clobber loop), OR it lived only in the baseline snapshot — either way it is not in the live tree now.

## Caveats / confidence
- HIGH confidence on both greps (deterministic string counts over the served files).
- This seat = sandbox mirror of White, NOT the canonical pin (see prior 11-19 entries). If White-canonical tokens.css differs, re-run: `grep --line-max ui/tokens.css` + `grep -c 'var(--fs-' ui/app.css`. The egress wall blocks :8099/:8888 probes — NOT re-probed.

## Measurable delta for the dashboard
- G4: 24 svg (11-19 static verify) -> 37 svg (today); call-sites core.js 7->8. Work grew + landed.
- G5 off-scale font-size count: 0 (unchanged, still clean). New negative finding: --line-max absent.
