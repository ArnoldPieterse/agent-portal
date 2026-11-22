# UI Asset Inventory Correction
**Author:** Designer | **Date:** 2026-11-23 | **Type:** self-correction
**Parent:** memory/designer/INDEX.md
**Related:** memory/ops/ui-asset-inventory-2026-11-23.md

## What was wrong
Initial UI asset inventory (written same day) listed tokens.css as "never loaded by browser" and reported a false bug: --agent-purple allegedly undefined in the live page.

## Root cause of error
Missed `@import "tokens.css";` at line 1 of ui/app.css. This means the browser DOES fetch tokens.css (as a secondary CSS request after parsing app.css), so all 117 token vars including --agent-purple resolve correctly.

## Correction applied
- Loaded file count: 7 to 8 (added tokens.css)
- Dead file count: 14 to 13 (removed tokens.css from dead list)
- "Bug Found" section retracted with explanation
- Active payload updated: ~145 KB to ~147 KB

## Verification
```
grep -n "@import" ui/app.css
# L1: @import "tokens.css";
```
Portal handler (agent_portal.py L4920-4924) serves any *.css from ui/ matching the regex, so /ui/tokens.css returns 200.

## Lesson for future audits
Always check for @import and url() references in loaded CSS before classifying sibling files as dead code.
