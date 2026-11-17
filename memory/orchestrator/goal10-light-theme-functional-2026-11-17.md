# Goal #10 — light theme made functional (2026-11-17)
Owner: Orchestrator | Status: PARTIAL progress (code step done + statically verified; NOT closed)

## What was broken
Goal #2 (Designer) had already added a `data-theme` toggle in ui/core.js, but light mode never rendered:
- core.js initTheme set `data-theme="dark"` for dark and REMOVED the attribute for light.
- ui/app.css had NO `[data-theme=light]` block; `:root` is the dark family.
- Net effect: choosing "light" removed the attribute -> fell back to dark `:root`. The toggle visually did nothing on the light leg.

## Fix (this pass)
1. ui/app.css — added `[data-theme=light]{ ... }` with 12 LITERAL color tokens (no var() aliases, per the documented rule that a var() cycle invalidates every token at computed-value time). All :root color tokens covered: bg,panel,panel2,line,text,dim,acc,ok,warn,err,focus,faint.
2. ui/core.js — fixed initTheme mapping to the CSS convention (`data-theme="light"` = light; no attribute = dark) and rewrote the toggle handler so it flips correctly (light->dark removes attr + stores "dark" + shows sun; dark->light sets attr + stores "light" + shows moon). Persistence key unchanged: localStorage "portal-theme".

## Verification (in-sandbox, static — no network/browser needed)
- [data-theme=light] block present in ui/app.css: True
- var() aliases inside the light block: 0 (no cycle)
- :root color tokens missing from light block: 0 (all 12 covered)
- core.js paren/brace balance: 0 / 0 (bracket -1 is pre-existing string content; this edit added zero [ ])
- Convention now consistent end-to-end: JS attr <-> CSS selector.

## Remaining (why NOT closed)
- (a) 480px phone breakpoint — goal #10 wants tablet(768)+phone(480); app.css already has @media(max-width:768px) and (max-width:375px), needs a 480px rule.
- (b) live-viewport render + no-horizontal-overflow check at 480px — needs a browser; sandbox egress/no-browser class, ALREADY logged once in memory/ops/blockers.md (do NOT re-probe).
- (c) ~28 hardcoded hex literals outside tokens (see appcss-hardcoded-colors-verify-2026-11-17.md) don't adapt in light mode — broader tokenization follow-up.

## Files changed
- ui/app.css (light block inserted directly after :root)
- ui/core.js (initTheme mapping + toggle onclick handler)
