# Goal #1 - Design Token System wired (root-cause fix) - 2026-11-19

## Finding (the real blocker)
tokens.css was **never loaded by the page**. index.html links only `ui/app.css`; app.css had no
`@import`, and carried its own inline `:rootEllipsis` subset of tokens. So every component reference
to a token that lived ONLY in tokens.css (`--sel-bg`, `--peek-tx`, `--dm-text`, `--dot-*`, etc.)
was silently resolving to nothing. The tokens.css header comment ("Loaded via @import at top of
app.css") was aspirational, not true.

## Fix (this pass)
1. Added `@import "tokens.css";` at the very top of app.css (before any rule; comments may precede it).
2. Removed the duplicate inline `:rootEllipsis` block from app.css - tokens.css is a strict superset
   with identical dark values, so nothing was lost.
3. Promoted the 8 remaining raw literals in component rules to new tokens + light overrides:
   --busy --qspin-bd --qspin-top --qtxt (dark) and their [data-theme=light] values.
4. Replaced all 28 raw hex/rgba values across app.css component rules with var(--token).

## Verification (hard evidence)
- Python scan: **app.css = 0 hex-color literals**; tokens.css = 74 (dark :root + light block).
- Token resolution check: 51/51 referenced `var(--*)` in app.css are defined in tokens.css.
  The only "dangling" hit was the literal string `var(--token)` inside a comment - false positive.
- Net effect: dark theme computed styles unchanged (identical values); light theme now ACTUALLY
  applies (previously a no-op because tokens.css wasn't loaded).

## Acceptance status
Goal #1 stated test = "grep hex in ui/*.css returns 0 hits outside tokens.css; components use var()".
CSS-scope acceptance: MET. (JS inline-style hex, if any, is out of the *.css test scope.)
