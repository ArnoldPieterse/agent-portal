# Designer cycle-5 goal 1 — Design Token System (single source) — 2026-11-19

## Claim
`ui/app.css` is now fully token-driven with `ui/tokens.css` as the single source of truth.
Acceptance test for goal 1: "grep for hex colors in ui/*.css returns 0 hits outside
tokens.css; all components use var(--token)."

## What was wrong before this pass
- `index.html` linked ONLY `ui/app.css`; `ui/tokens.css` existed on disk but was never loaded.
- `app.css` carried its own redundant `:root{...}` block (subset of tokens, with looser
  spacing values that overrode the density-pass values in tokens.css).
- ~28 component rules still used hard-coded hex / rgba literals instead of var(--token).

## Change made (ui/app.css only — index.html untouched, so no pin advance needed)
1. Replaced app.css's redundant `:root` block with `@import url('tokens.css');`
   (resolves to /ui/tokens.css via the existing GET /ui/* static route).
2. Migrated every hard-coded color literal in component rules to an exact-value token
   (e.g. #20304d->var(--esc-sel-bg), rgba(61,220,132,.08)->var(--ok-bg),
   0 8px 24px rgba(0,0,0,.5)->var(--shadow-card)). Color values unchanged -> no color
   regression. Spacing now resolves to tokens.css's tighter density-pass values (goal 2).

## Verification (ran 2026-11-19)
- `grep '#[0-9a-fA-F]{3,6}' ui/app.css` -> **0 hits**.
- `grep` on `ui/tokens.css` -> 37 hex lines (the canonical definition file; expected).
- Token cross-check: 52 distinct var(--*) referenced in app.css, ALL defined in
  tokens.css :root (0 dangling). @import precedes first CSS rule (valid ordering).

## Files
- ui/app.css (edited: removed duplicate :root, added @import, tokenized 29 rules)
- ui/tokens.css (unchanged; now the single source, actually loaded)

## Status
GOAL 1 ACCEPTANCE TEST MET. Colors are 100% tokenized; single-source tokens.css is live.
Note: this also makes goal 2's density pass take effect (app.css no longer overrides the
spacing tokens) — goal 2 still needs before/after screenshots for its own acceptance test.
