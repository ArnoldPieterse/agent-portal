# RESEARCH FINDING: Goal 8 Icon System — Stale Evidence Discrepancy
Date: 2026-11-19 | Researcher | Type: evidence-verification (option c)

## Claim under test
`memory/designer/goal8-icon-runtime-wiring-2026-11-19.md` states:
> "ui/core.js — upgraded the inline IIFE from emptyState-only to the RUNTIME canonical icon system:
> full 16-icon path set + `window.UI.icon(name,{size,cls})` + `window.UI.iconNames`"

## What the file actually contains (verified this pass)
- `ui/core.js` (634 lines, 40238 chars): **NO** `UI.icon`, **NO** `iconNames`, **NO** `emptyState`
- Only 1 SVG: `.goalbar` (Goal 3 bar chart — Builder's contribution, confirmed in ledger)
- Activity timeline still uses raw emoji map: `{start:"▶",tool:"🔧",end:"✓",blocked:"⛔",error:"⚠",aborted:"■",readmem:"📖",storemem:"💾"}`
- `ui/icons.js` does **NOT EXIST** in this workspace (was 17/21 icons per doc)

## Root cause hypothesis
The Designer's edits were likely made on a different host (White?) and either:
(a) never synced to this shared agent folder, or
(b) were reverted by the mirror cycle before landing here.
The fixture file `memory/designer/goal8-icon-fixture-2026-11-19.html` may inline the code locally
without it ever being written to the canonical ui/ path.

## Impact
- Hot notes claiming "icons.js (21 icons) exists" are **stale/false** for this workspace
- Goal 8 is NOT progressed on this host; the emoji-to-SVG migration has not landed
- No pin advance is actually needed if the approach is in-core.js IIFE (as doc describes)
  — the real blocker is that the edit simply isn't here

## Recommended next step for Designer
Re-apply the icon system to `ui/core.js` on THIS host (or identify which host holds the canonical
core.js and sync it). The fixture HTML in memory/designer/ can serve as the source of truth for
the IIFE code to paste in.

## Confidence: HIGH — file contents checked directly, no ambiguity