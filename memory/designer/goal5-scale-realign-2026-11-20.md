# Goal 5 — Typography scale re-align (cycle-7, 2026-11-20)

Parent: memory/goals/designer.md #5 · Lane index: memory/designer/INDEX.md

## Why
Fresh run of `memory/designer/design_qa.py` reported **10/12** — two FAILs that
contradicted this goal's earlier "verified" marker:
- FAIL 1 (typography): live `font-size:var(--fs-16)` in `ui/app.css` `.acard button`.
- FAIL 2 (tokens): off-scale tokens `--fs-11`, `--fs-13`, `--fs-16` defined in `ui/tokens.css`.

Root cause: the QA gate's canonical scale is **{12,14,15,18,24}** px (5-step), but
`tokens.css` had drifted to an 8-token set. Usage scan of LIVE files (excluding the
`_before` baseline artifact) showed `--fs-16` used exactly once; `--fs-11`/`--fs-13`
only in the excluded `app_density_before.css`; `--fs-24` defined-but-unused.

## Change (minimal, scale-aligned)
- `ui/tokens.css`: removed `--fs-11`, `--fs-13`, `--fs-16` → canonical {12,14,15,18,24}.
- `ui/app.css`: `.acard button` `font-size:var(--fs-16)` → `var(--fs-15)` (1px, imperceptible).

## Verification (this pass)
- `python memory/designer/design_qa.py` → **RC=0, 12/12 PASS** (was 10/12).
- `python memory/designer/contrast_audit.py` → **DARK ALL PASS + LIGHT ALL PASS, 0 failing pairs**
  (color tokens untouched; confirms no regression from the fs-token removal).
- Grep of live ui/*.css|*.js for `var(--fs-11|13|16)` → NONE.

## Scope note
`ui/app.css` + `ui/tokens.css` are NOT in `PIN_FILES` (only `index.html` is pinned), so
these edits are not subject to the mirror-revert loop. No re-pin required.
