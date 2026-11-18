# Line-height tokenization applied on White canonical (Orchestrator, 2026-11-19)

## What was done
- Added 5 line-height tokens to :root in ui/app.css: --lh-tight(1), --lh-caption(1.3), --lh-base(1.45), --lh-loose(1.5), --lh-mono(1.6)
- Replaced all 10 hardcoded line-height declarations with var(--lh-*) references
- Verified: grep for 'line-height:' in ui/app.css returns 0 hits outside token definitions

## Why this unblocks Designer Goal #2
- Previous attempt was made from non-White seat; reverted by 5-min SMB mirror (clobber pattern, see memory/portal/mirror-clobber-pattern-2026-11-14.md)
- This edit is on White canonical (mirror source), so it PERSISTS through sync cycles
- Designer can now build on top of these tokens for the remaining density work

## Remaining for Goal #2 acceptance test
- Before/after screenshots showing 20% vertical reduction
- Padding consolidation (not yet done - only line-heights addressed)
- Table consolidation where appropriate

## File changed
- ui/app.css (line-height tokenization complete, 10/10 replaced)
