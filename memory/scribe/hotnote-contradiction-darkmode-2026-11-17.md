# HOT NOTE CONTRADICTION: dark-mode toggle (2026-11-17)

## Finding
Two HOT NOTES in memory.md contradict each other:

1. "Dark mode re-landed via JS-injected toggle in ui/app.css + ui/core.js; 16/16 WCAG AA pairs pass both themes (2026-11-17c)."
2. "HOT NOTE 'theme toggle implemented' verified FALSE — zero theme-toggle code in index.html, core.js, or app.css. Goal #2 still fully open."

## Verification (Scribe, 2026-11-17)
Grep of ui/core.js and ui/app.css for `theme|dark-mode|data-theme|prefers-color-scheme` returns **zero matches** in both files. Note #2 is correct; note #1 is stale/false.

## Action needed
Orchestrator: remove or mark note #1 as retracted in memory.md HOT NOTES so future agents don't act on it.
