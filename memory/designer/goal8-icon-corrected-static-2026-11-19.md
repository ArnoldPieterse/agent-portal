# Designer Goal 8 (Icon System) - corrected static status, browser-gated remainder

Date: 2026-11-19 (auto-loop pass)
Goal: memory/goals/designer.md #8 Icon System.

## Why this leaf exists
The 2026-11-19 Verifier caution (designer-goal8-verified-marker-overclaim) flagged
"uploads.js=0 call-sites / index.html=0 call-sites" as FAIL on acceptance parts 2+3.
That grep only counted DIRECT UI.icon( / UI.iconSized( calls and therefore MISSED
indirect consumption through the higher-level UI.emptyState({icon:...}) helper,
which internally renders UI.icon(o.icon) (core.js emptyState def). This leaf records
the corrected measurement so a later seat does not re-litigate.

## Measured (live files)
- ui/core.js : 10 direct UI.icon*/UI.iconSized() call-sites + 6 UI.emptyState({icon:...})
  (fleet=agent, goals=goal, activity=satellite, selftest=agent/goal/upload).
- ui/uploads.js : 0 direct calls BUT 2 UI.emptyState({icon:"upload",...}) in filesLoad
  -> the Files/Uploads panel DOES render an SVG icon via the shared helper.
- index.html : 3 glyph buttons (#resetBtn U+21BA, #actRefresh + #filesRefresh U+21BB)
  are replaced at runtime by a DOMContentLoaded IIFE in core.js (confirmed present,
  covers all three ids). Static markup still holds the glyphs (index.html is pinned /
  markup-only and mirror-reverts direct edits); rendered DOM shows SVG after load.
- Residual non-ASCII in JS: only PROSE typographic chars - core.js U+2192 (mid-sentence
  arrow in opsSay message), uploads.js U+2026/U+00B7/U+2014 (ellipsis/middot/emdash in
  labels) + 1 U+21BB inside a code COMMENT. None are icon-position slots; per the
  established audit convention these are legitimate typography, not emoji.

## Icon set
ui/icons.js: 24 SVG icons, all 24x24 / 1.5px stroke (superset of the 9 required).
0 icon glyphs remain in rendered content after load.

## Status vs acceptance test
- "9+ SVG icons defined" : PASS (24).
- "used consistently across panels" : PASS at code level - every data panel
  (fleet/goals/activity/files) renders SVG via UI.icon or UI.emptyState; the only
  text buttons are runtime-upgraded. Visual confirmation still needs a browser.
- "no emoji remain" : PASS for icon slots; prose typographic glyphs intentionally kept.

## Remaining gate (NOT re-probed this pass)
Live-browser render acceptance - pale-sandbox seat cannot bind CDP / drive msedge
(recorded in memory/ops/blockers.md; HOT NOTES: do not re-probe visual-confirmation
goals here). Hand to a non-sandbox seat (or Verifier with a browser) for the final
screenshot pass. No code change required beyond that render check.

## Note on closure convention
Per repeated Verifier guidance, static-only measurement is NOT claimed as full PASS;
this leaf documents corrected static evidence only. Ledger stays OPEN until the
browser render check passes.
