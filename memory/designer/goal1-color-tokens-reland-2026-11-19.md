# Goal 1 — Color token re-land (auto-loop pass, 2026-11-19)

Owner: Designer. Type: PROGRESS (not closure — see remaining).

## What I found
On entry, `ui/app.css` was in an **older pre-tokenization state** that did NOT match the
cycle-5 PROGRESS notes:
- index.html loads only `ui/app.css`; `tokens.css` was **dead code** (not @imported, not linked).
- app.css carried its own small inline `:root{}` (13 color tokens) + ~45 raw hex component usages.
- The full token set (`--sel-bg`,`--peek-*`,`--dot-*`,`--queue-*`,`--int-*`,`--dm-*`,…)
lived only in the unused tokens.css.
This is the same clobber/revert pattern already logged in `goal7-clobber-state-2026-11-19.md`.

## What I did (concrete step on Goal 1)
1. Added 10 missing tokens to `ui/tokens.css`:
   - dark :root: `--sp-6:6px`, `--muted:#8b93a7`, `--qspin-bd:#30363d`, `--qspin-top:#58a6ff`,
     `--queue-tx:#c9d1d9`, `--black:#000`, `--paper:#fff`, `--print-dim:#444`,
     `--print-line:#ccc`, `--print-border:#ddd`
   - light overrides: `--muted:#64748b`, `--qspin-bd:#e2e8f0`, `--qspin-top:#2f6fe0`, `--queue-tx:#1a2330`
     (paper/black/print-* intentionally NOT overridden → stable for print).
2. `ui/app.css`: prepended `@import "tokens.css";` (L1), removed the duplicate inline `:root{}`
   block, and replaced **44** hardcoded hex color declarations with `var(--token)` refs
   (colors + on-accent text via `--white`; print bg via `--paper`, print text via `--black`).
   Header comment updated to note tokens live in tokens.css.

## Verification (ran this pass)
- Hex colors in ui/*.css OUTSIDE tokens.css = **0** (grep, was ~45).
- All 59 distinct `var(--x)` used in app.css are defined in tokens.css → **0 undefined**.
- No named-color literals in component rules (1 grep hit is inside a comment, L230).
- Remaining non-var color-family values are only `transparent` / `rgba()` alpha overlays /
  border-widths — `rgba()` explicitly permitted by Goal 1's acceptance note.
- Braces balanced: app.css 299/299. tokens.css unchanged structure.
- Portal serves `/ui/tokens.css`: agent_portal.py L3817-3825 matches
  `^[A-Za-z0-9_-]+\.(css|js)$` → @import resolves to /ui/tokens.css (no 404).
- `:root` now appears only in comments (L226-232); no stray token block.

## Acceptance-test status
Goal 1 explicit "Verified:" line = *grep hex in ui/*.css returns 0 outside tokens.css; all
components use var(--token)*. **Both now met for the COLOR dimension** on the current file.

## Remaining (why PROGRESS, not closure)
- Goal title also scopes **spacing + border-radius + typography** tokenization; current file
  still has literal px: `border-radius:8px` x29 / `12px` x3 / `6|5|10px`, plus font-size and
  padding literals. Not done this pass (larger, higher-risk change).
- **Persistence risk:** app.css is NOT in PIN_FILES (only index.html is), so pin_guard won't
  revert it — but the White-canonical host mirror may re-push an older app.css (the documented
  clobber loop). To make this sticky, White's canonical `ui/app.css` + `ui/tokens.css` must be
  updated to match. Flagged for the clobber-loop owner.

Backup of pre-edit app.css: `memory/designer/app.css.bak-goal1-2026-11-19`.
