# Goal #2 (Information Density Pass) - acceptance-path unblock, 2026-11-19 (Designer auto-loop)

## What was wrong
The `#selftest` density harness in `ui/core.js` (`UI.density`, lines ~478-502) measures the
density goal by swapping the live `<link rel=stylesheet>` to `/ui/app_density_before.css`,
measuring `scrollHeight` of `body` + `fleetBody`/`goalsBody`/`filesList` as "before", then
restoring `app.css` for "after" and computing per-panel `reduction_pct` vs the 20% target.

That baseline file **did not exist** (`ui/` held only `app.css` + `tokens.css`), so the swap
404'd: the before-state was never measurable, meaning the goal #2 acceptance test could not
run even when a real browser session is available. This is distinct from (and upstream of)
the shared "no headless browser on host" blocker - the harness itself was broken.

## What I did
1. Confirmed `agent_portal.py` serves `/ui/<name>` for any name matching
   `^[A-Za-z0-9_-]+\.(css|js)$` (line ~4032) -> `app_density_before.css` is route-serveable.
2. Identified the true pre-density baseline: `memory/designer/app_css_CANONICAL_7cb6a62d6e92_2026-11-18d.css`
   (hardcoded line-heights 1.3/1.45/1.5/1.6/1.7, pre-spacing-tokenization - the state before
   the density pass began).
3. Created `ui/app_density_before.css` = that canonical + a header documenting its purpose.
   Kept it standalone (no `@import tokens.css`) so it carries the old literal values as the
   before-state; newer feature CSS (tour/toast/skeleton/goalbar) postdates it and is absent by
   design - those rules simply won't match in the before-state, which is correct for measuring
   the density delta on existing panels.
4. Confirmed `memory_mirror.py` `pin_guard()` protects only PIN_FILES (index.html); a new ui/
   file has no mirror-revert risk.

## Static verification (no browser needed)
- File written: `ui/app_density_before.css`, 25,901 bytes.
- Route regex match: `re.match(r'^[A-Za-z0-9_\-]+\.(css|js)$','app_density_before.css')` -> True.
- Real density delta present in current app.css vs this baseline (diff of density props):
  `#actBody` line-height `1.7 -> var(--lh-loose)` (=1.5, -12% on the largest panel);
  `.opsbox`/`.ft-models` `1.6 -> var(--lh-mono)`; `.sub`/`.ft-tooltip` `1.5 -> var(--lh-loose)`;
  `.mh-d` `1.3 -> var(--lh-caption)`. So the harness will measure a genuine reduction, not zero.

## Still open (NOT closed - acceptance test has NOT passed)
- Run `index.html#selftest` in a **live browser session** and read `#selftestOut`
  (`SELFTEST_JSON ... density.panels[].reduction_pct` / `body_reduction_pct`) to confirm >=20%
  with no clipping. Shared NEEDS-HUMAN: no headless browser on host (blockers.md); not re-probed.

## Artifact
- Created: `ui/app_density_before.css`
- Source baseline: `memory/designer/app_css_CANONICAL_7cb6a62d6e92_2026-11-18d.css`
