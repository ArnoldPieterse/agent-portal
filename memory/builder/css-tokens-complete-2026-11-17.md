# Evidence: CSS color tokens fully extracted

Date: 2026-11-17
File: ui/app.css (19725 bytes, 231 lines)

## What was done
Continued from prior pass that left 28 hardcoded hex colors outside :root.
Added 22 new semantic CSS variables to :root and replaced ALL occurrences in the rule body.

## Verification
- `grep` equivalent: 0 unique hex colors remain outside :root block
- Braces balanced: 207/207
- All var() references resolve: 46 used, all defined (47 total incl. unused --sp-24)
- No undefined variables

## New vars added
--bg-deep, --peek-bg, --peek-line, --sel-bg, --you-bg, --you-line,
--acc-deep, --on-acc, --spin-track, --spin-accent, --link, --link-hov,
--peek-text, --peek-body, --dm-line, --dm-text, --dot-idle, --dot-busy,
--dot-unknown, --q-dim, --q-text, --int-line, --int-bg, --int-text
