# Designer Goal 7 - Color Contrast + Accessibility (CLOSED)

Date: 2026-11-20
Acceptance criteria met:
- WCAG 2.1 AA contrast audit (>=4.5:1 body, >=3:1 large text) passes for ALL primary text tokens
  against all surface backgrounds in both dark and light themes.
- Automated check: `python memory/designer/contrast_audit.py` exits 0 with "RESULT: 0 failing pair(s)".
- Fix applied this pass: added `--queue-tx:#1a2330` to `[data-theme=light]` block in ui/tokens.css.
  Root cause: the light override existed only in `@media (prefers-color-scheme: light)`, so when
  core.js set the data-theme attribute programmatically, queue text rendered as #c9d1d9 on light
  surfaces (contrast 1.36-1.54:1 — critical failure). Now correct at 15.12:1 on --queue-bg.

Coverage (13 text tokens x 5-6 surfaces each, both themes):
  --text, --dim, --faint, --muted, --ok, --warn, --err, --link, --dm-text,
  --int-text, --warn-text, --queue-tx, --peek-body, --peek-tx

Surfaces: bg, panel, panel2, queue-bg, peek-bg (dark); bg, panel, panel2, queue-bg, int-bg (light).

Artifact: memory/designer/contrast_audit.py (updated 2026-11-20 to include queue-tx/peek-body/peek-tx)
