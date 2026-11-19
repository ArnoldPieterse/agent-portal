# Goal 8 - Icon System: Button Label Wiring (auto-loop pass)
Date: 2026-11-19
Agent: Designer

## What was done
Wired all 12 visible emoji button labels in index.html to the SVG icon system:

1. icons.js: Added 3 new icons (clock, refresh, push) -> 25 total (was 22)
2. index.html: Replaced emoji in 12 button/h1 positions with
   <span class="ico" data-icon="name">emoji</span> (emoji kept as noscript fallback):
   - robot (h1), goal, clock, satellite, folder, wrench, close (reset), stop,
     refresh x2, push, scissors, close (dialog)
3. core.js: Added DOMContentLoaded handler that finds all [data-icon] spans
   and replaces content with UI.iconSized(name, 14)
4. app.css: Added .ico{display:inline-flex;...width:14px;height:14px} + .ico svg rules
5. Pin advanced: index.html -> 6b50b06fa0e8

## Verification (static)
- All 11 data-icon values have matching ICONS definitions in icons.js [PASS]
- Braces balanced in all modified files [PASS]
- Pin sha matches current file + backup [PASS]

## Remaining for full closure
- 14 warning/check inline text indicators in textContent contexts (core.js, uploads.js) -
  these are typographic status markers ("[warn] Error: ..."), not icon-position elements.
  Converting requires textContent-to-innerHTML restructure (larger refactor).
- uploads.js L94: warning as addBubble() icon param - needs API change to accept HTML.
- Browser rendering acceptance test (shared blocker with #5/#10).

## Files changed
- ui/icons.js (+3 icons)
- index.html (12 emoji -> data-icon spans)
- ui/core.js (DOMContentLoaded icon init)
- ui/app.css (.ico CSS rules)
- memory_mirror.py (pin advance)
