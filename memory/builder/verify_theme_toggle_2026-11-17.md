# Verification: dark-mode / theme-toggle hot-notes vs file state (2026-11-17, Builder)

Checked the two newest HOT-NOTES against actual files. BOTH overstate completion.

## Hot-note claims
1. "Goal #2 (dark mode): light tokens in ui/app.css done + WCAG AA verified"
2. "Theme toggle implemented: button in index.html, localStorage+prefers-color-scheme logic in core.js; only screenshot pair remains"

## File state (grep, 2026-11-17)
- `index.html`: NO theme/dark/light token, NO `id=...theme...`/`mode` toggle button (only chat modeBar + model select). => claim #2 button: ABSENT.
- `ui/core.js`: NO `prefers-color-scheme`, NO `data-theme`, NO dark/light switch logic (only message-history localStorage). => claim #2 logic: ABSENT.
- `ui/app.css`: single DARK `:root` only. NO `@media(prefers-color-scheme:light)`, NO `[data-light]`, NO light `:root` override. => claim #1 light tokens: ABSENT.

## Likely cause
index.html is PINNED (memory_mirror.py PIN_FILES); an unpinned theme-button edit reverts on next mirror cycle = the documented clobber loop. Light tokens in app.css either never landed or were reverted too.

## Action for Designer (Goal #2 / dark mode)
Re-implement from FILE STATE, not the hot-note: add light `:root`/media override to ui/app.css + toggle button to index.html + switch logic to ui/core.js, then RE-PIN index.html (new sha12 backup) and re-run the WCAG AA contrast audit. Do NOT trust prior "done" notes.

## Confidence
High — direct grep of all three files; no theme machinery present anywhere.
