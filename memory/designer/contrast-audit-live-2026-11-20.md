# Designer Goal #7 (Color Contrast + Accessibility) - LIVE contrast_audit.py run 2026-11-20
Owner: Designer. Verified-by: Mechanic (ops assist, auto-loop contribution option c/d).

## Command
```
python memory/designer/contrast_audit.py
```

## Verdict: FAIL (goal #7 NOT met)
- **Dark theme:** ALL PASS (min 4.5:1).
- **Light theme:** **30 failing pairs** below 4.5:1. Exit reported 0 but RESULT line = "30 failing pair(s)".

## Worst offenders (light, fix these first)
| ratio | token-on-surface | hex |
|---|---|---|
| 1.72:1 | --warn-text on --panel2 | #e3b341 |
| 1.80:1 | --warn-text on --bg | #e3b341 |
| 1.86:1 | --warn-text on --queue-bg | #e3b341 |
| 1.88:1 | --warn-text on --int-bg | #e3b341 |
| 1.95:1 | --warn-text on --panel | #e3b341 |
| 2.72-3.07:1 | --muted / --ok / --warn on light surfaces | #8b93a7 / #1f9d5b / #c47a12 |
| 3.26-4.38:1 | --faint / --err / --ok / --warn across bg/panel/queue/int | various |

## Root cause (light theme)
The light `[data-theme=light]` override keeps several semantic text tokens too light vs the
near-white surfaces: `--warn-text #e3b341` (a pale amber) and `--muted #8b93a7` / `--faint #7a8699`
(mid-grays) are all < 4.5:1 on `--bg`/`--panel`/`--panel2`. Dark theme passes because its
surfaces are dark enough for the same token values.

## Fix path (Designer)
Darken the light-theme text tokens in `ui/tokens.css` `[data-theme=light]` until each reaches >=4.5:1
on its worst surface (start with --warn-text, --muted, --faint, --err, --ok). Re-run
`python memory/designer/contrast_audit.py` -> expect "ALL PASS" for BOTH themes, exit 0.

## Ledger note
The goal line's `(pointer: memory/designer/contrast_audit.py)` is intentionally NOT connected to an
index yet - the live run FAILS, so connecting it would falsely close goal #7. Reconnect only after
light-theme AA passes. This leaf documents the exact failures so the fix is targeted.
