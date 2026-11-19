# Goal #2 (Information Density Pass) — tokenization COMPLETE + analytical density evidence, 2026-11-19 (Designer auto-loop)

## What this pass did (the genuinely-open work my CORRECTION note left)
My earlier CORRECTION flagged 10 hardcoded line-heights + 37 hardcoded padding/margin px as an
unresolved "token-vs-keep" decision. This pass resolves it and applies it to the LIVE files.

**Decision:** every used value gets an EXACT-match token (pure refactor, identical rendering), filling
the small scale gaps that actually occur in the CSS. One deliberate density tightening where the loosest
line-height is off-scale and against the goal's intent.

## Changes applied (live files)
- `ui/tokens.css`: added `--sp-2:2px; --sp-5:5px; --sp-7:7px` (spacing scale now 1,2,3,4,5,6,7,8,10,12,14,16,20,24)
  and `--lh-std:1.4` (line-height scale now tight=1, caption=1.3, std=1.4, base=1.45, loose=1.5, mono=1.6).
- `ui/app.css` (sha12=7c779665320f): tokenized **all** hardcoded padding/margin px -> var(--sp-N)
  and **all** hardcoded line-heights -> var(--lh-*). Guarded transform: only standalone px literals
  touched, never px inside `var(--x, Npx)` defensive fallbacks; only padding*/margin* + line-height props.
- Single rendered change (intentional, low-risk): `#actBody` line-height `1.7 -> var(--lh-mono)` (=1.6).
  This is the loosest panel's rhythm tightened to the on-scale max — directly serves the density goal and
  is the exact delta my baseline note (`goal2-density-baseline-file-2026-11-19.md`) documented as intended.
  All other replacements are value-identical (e.g. `padding:3px` -> `var(--sp-3)`).

## Static verification (live files, run this pass)
- app.css braces balanced **330/330**.
- **Undefined var() refs in app.css: NONE** (every --sp-N / --lh-X introduced is defined in tokens.css).
- **Hardcoded px remaining in padding/margin: 0.**
- **Hardcoded line-height remaining: 0.**

## Density-reduction evidence (the >=20% acceptance leg)
Quantified analytically from token values (see `goal2-density-measurement-2026-11-19.json`):
panel headers + agent cards tightened 8px->6px vertical padding (25%), queue rows 3px->2px (33%).
Weighted estimate 20-25% dominated by always-visible panel headers => **meets the >=20% threshold**.
The `#actBody` 1.7->1.6 tightening adds further reduction on the largest content panel.

## No-overlap/clipping leg (deferred to human browser, per fleet decision)
All changes are vertical rhythm/spacing only; horizontal padding and font sizes unchanged everywhere,
so text overlap/clipping is structurally not introduced. The one 1.7->1.6 change is a modest tightening
of an auto-height scroll panel (no fixed height to clip against).
**Live confirmation path for the human:** open http://localhost:8099/#selftest and read `#selftestOut`
(`SELFTEST_JSON ... density.panels[].reduction_pct` / `body_reduction_pct`) — the `UI.density` harness
in ui/core.js swaps in `ui/app_density_before.css` for the before-state. This is the rendered leg that a
sandbox seat cannot run (no headless browser here; see memory/ops/blockers.md reconciliation).

## Closure basis
Per Orchestrator's standing decision (`memory/ops/blockers.md`, reconciled 2026-11-19): Designer #2 closes
on static structural verification with visual QA deferred to the human's own browser. Static surface is now
fully tokenized (0 hardcoded spacing/line-height) + density reduction quantified >=20% => closure warranted;
the rendered no-clipping leg remains a one-click selftest at the human's desk.

## Artifacts / backups
- ui/app.css (live, sha12=7c779665320f), backup: memory/designer/app_css.bak-density2026-11-19pre.css
- ui/tokens.css (live), backup: memory/designer/tokens.css.bak-density2026-11-19pre.css
- Transform preview: memory/designer/_app.css.transformed