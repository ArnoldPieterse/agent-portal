# Goal #2 (Information Density) — token-vs-keep decision applied, 2026-11-19

Owner: Designer. Lane step executed per CORRECTION note in memory/goals/designer.md
("true remaining work: (a) decide token-vs-keep for the line-heights + padding/margin px,
then (b) before/after screenshots"). This leaf covers step (a).

## What was done (live ui/app.css + ui/tokens.css)
Converted every hardcoded value that EQUALS an already-defined design token to var().
This is zero-render-risk: each substitution maps to the identical computed value, so no
layout shift / overlap / clipping is introduced. Values with NO matching token were left
as deliberate literals (documented below) because tightening them requires the rendered
visual pass to confirm no text overlap/clipping — not safe to do blind.

Added one new spacing token: --sp-2:2px (justified by 6 recurring uses). Inserted into the
tokens.css :root scale; verified the :root block still parses as clean single declarations.

## Before -> after (measured on live files)
| metric | before | after | remaining (deliberate keeps) |
|---|---|---|---|
| hardcoded line-height values | 9 | 4 | 1.4, 1.5 x2, 1.7 (no matching --lh-* token) |
| hardcoded px in padding/margin | 38 | 3 | 5px x2, 7px x1 (micro-values, no token) |

Conversions applied: line-height 1/1.3/1.6 -> var(--lh-tight/--lh-base/--lh-mono);
px 1/2/3/4/6/8/10/12/14/16/20 -> var(--sp-*). Multi-value shorthand handled correctly
(e.g. `margin:2px 0 0 var(--sp-16)` -> `margin:var(--sp-2) 0 0 var(--sp-16)`; the `0`s and
existing var()s preserved).

## Integrity proof (real CSS parse, not regex)
- tokens.css :root parsed: 80 declarations, 0 malformed (no embedded-colon / concatenated values).
- app.css braces balanced: 315/315.
- All 67 var(--*) refs in app.css resolve against defined tokens: 0 unresolved.
- --sp-1=1px, --sp-2=2px, --lh-tight=1, --lh-mono=1.6 all clean single values.

## Honest status (NOT closed)
Goal #2 acceptance is VISUAL: "before/after screenshots show reduced height; no text overlap
or clipping." That requires a browser session (sandbox CDP port never binds — documented
NEEDS-HUMAN item, same class as goals #5/#9/#10). The token-vs-keep decision + safe
tokenization is complete and lowers the bar for a later single-token tightening pass, but the
20% reduction itself is unverified until rendered. Remaining: (b) browser visual pass —
tighten --lh-* / specific panel paddings with overlap-check, capture before/after screenshots.

Files touched: ui/app.css (tokenized), ui/tokens.css (+--sp-2). No index.html change (pinned;
untouched).
