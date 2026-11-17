# Goal #2 Dark Mode - Progress (2026-11-17)

## What was done this pass
1. app.css: Added [data-theme=light] block with 24 light-mode token overrides.
2. app.css: Tokenized 6 previously-hardcoded color values (msg.you, seg.on, peek, flink, dmseg).
3. core.js: Appended initTheme() IIFE - creates toggle button, localStorage persistence, prefers-color-scheme fallback.

## Still remaining for full acceptance
- Screenshot pair (dark + light) on :8099
- WCAG AA contrast script re-run on both themes, 0 failures

## Artifacts
- ui/app.css (light block + tokenized rules)
- ui/core.js (initTheme at EOF)
