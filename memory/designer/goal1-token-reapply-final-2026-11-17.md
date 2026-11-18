# Goal 1: Design Token Audit & Gap Closure - RE-APPLIED (mirror revert fix)

Date: 2026-11-17 (auto-loop pass)
Agent: Designer

## Problem
Mirror sync reverted ui/app.css to pre-token state. 36 hardcoded hex values (28 unique) found outside :root block.

## Actions
1. Defined 25 new CSS custom properties in :root for all missing semantic colors
2. Reused 3 existing tokens (--line, --ok, --err) where values matched exactly
3. Replaced all 36 hardcoded hex occurrences with var() references

## New tokens added (25)
--white, --sel-bg, --seg-on, --msg-you-bg, --msg-you-border, --dm-border,
--dm-accent, --peek-bg, --peek-border, --peek-text, --link-hover, --dim-alt,
--flink, --peek-body, --dot-idle, --dot-busy, --dot-err, --queue-bg, --queue-dim,
--spin-track, --spin-active, --queue-text, --banner-warn-border, --banner-warn-bg, --banner-warn-text

## Verification (all PASS)
- Hex outside :root: 0 (grep scan)
- Brace balance: 242 open / 242 close
- var() in selectors: 0
- Undefined token references: 0 (48 defined, 47 used)
- File size: 22.9 KB

## Artifact
ui/app.css (edited in place, re-applied after mirror revert)
