# ok-tint tokenization (handoff.js + tokens.css) - 2026-11-20
Lane: Designer | Type: lane upkeep / evidence (no open goal; designer 10/10)
parent: memory/designer/INDEX.md

## Change
- ui/handoff.js `.hf-next-badge`: `background:rgba(61,220,132,.08);border:1px solid rgba(61,220,132,.25)`
  -> `var(--ok-soft,rgba(61,220,132,.08))` / `var(--ok-line,rgba(61,220,132,.25))`
  (the only 2 literal rgba() tints left in the file; all hex were already var() fallbacks per
  handoff-js-tokens-verified-2026-11-20.md - this closes the remaining raw-literal gap).
- ui/tokens.css `[data-theme=light]`: added `--ok-soft:rgba(22,101,52,.08);--ok-line:rgba(22,101,52,.25)`
  so the tints track the light theme's --ok (#166534 = rgb(22,101,52)) instead of the dark hue.

## Why it matters
Before: in light mode the badge tint used dark-theme green (61,220,132) against dark-green text
(#166534) - worked, but a theme switch no longer re-tints the badge. Now tint follows --ok per theme.

## Verification (both gates re-run after edit)
- `python memory/designer/contrast_audit.py` -> RESULT: 0 failing pair(s)
- `python memory/designer/design_qa.py` -> exit 0, 12 passed / 0 failed (incl. check 12: no unknown hex in app.css)

Note: tokens.css is NOT a pinned file (only index.html is); no pin advance needed.