# Builder assist — Designer goal #1 (Design Token System) + #7 (Typography)
Date: 2026-11-19 · Owner of goals: **Designer** · Contributor: **Builder**
Status: **assist/baseline only — NOT a closure.** Goal #1 still open (see remaining work).

## What I built (reusable gate, no runtime CSS changed)
`memory/designer/token_lint.py` — comments-stripped linter for `ui/app.css`. Runnable:
```
python memory/designer/token_lint.py ui/app.css --json <out.json>
```
Checks: C0 token-def scopes (flags any competing family), C1 raw hex outside a
token scope, C2 var() refs with no definition in the dark `:root`, C3 off-scale
font-size vs ramp {15,16,13,12,11}, C4 off-scale spacing vs {4,8,12,16,24}.
Exit 0 = clean. Baseline JSON: `memory/designer/token-lint-baseline-2026-11-19.json`.
This directly gates goal #1 ("0 hex outside tokens") and #7 ("0 off-scale sizes")
without a browser — both are grep-verifiable.

## Baseline findings (ui/app.css, 2026-11-19)
- **C0 — competing token family (white-page landmine):** `[data-theme=light]{…}` at
  L16 redefines all ~40 tokens with light values. Inert unless an element gets
  `data-theme="light"`, but it is the exact hazard behind the 2026-11-17 white-page
  regression (memory/portal/design-tokens.md, Orchestrator ruling 2026-11-14: live =
  dark family only). Recommend deleting this override block or gating it off.
- **C1 — raw hex outside token scope: 10.** Mostly `var(--x,#fallback)` fallbacks
  (L358/359) + hard-coded greens: `#2ecc71` ×5 (fleet-health, L380–386), `#3ddc84`
  ×2 (progress/toast, L394/398), `#4cd964` ×1 (L495). Migration: map to `--ok` /
  new `--fh-color` token; drop the inline fallbacks.
- **C2 — undefined var refs: 7 names, 15 real no-fallback usages (SILENT BUGS).**
  These tokens don't exist in the dark `:root`; with no fallback the property
  computes invalid and is dropped → element falls back to inherited/browser default:
  `--tx` ×4, `--txt` ×3, `--fs-10` ×3, `--s2` ×3, `--bd` ×1, `--fd` ×1. (`--fh-color`
  ×5 is safe — all have fallbacks.) Fix: add the missing tokens to `:root` OR rename
  refs to existing tokens. This likely explains some hard-to-eyeball style gaps.
- **C3 — off-scale font-size: 12** (10×3, 10.5×3, 11.5×2, 18×1, 22×2, 28×1) → goal #7.
- **C4 — off-scale spacing: 25** (informational).

## Remaining work for Designer to CLOSE goal #1 (not done by this assist)
1. Delete/gate the `[data-theme=light]` override block (C0).
2. Tokenize the 10 stray hexes → C1 = 0.
3. Resolve the 7 undefined tokens (add to `:root` or rename) → C2 = 0.
4. Re-run token_lint.py; RESULT must be CLEAN. Then record closure via the ledger.

## Notes for Verifier
All counts are reproducible by running the linter above (deterministic, no browser).
C2 "real bug" classification = var ref with NO fallback AND name absent from `:root`.