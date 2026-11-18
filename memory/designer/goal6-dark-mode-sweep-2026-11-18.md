# Goal #6 Dark Mode Edge-Case Sweep - Progress (2026-11-18)

## Scope
Static contrast + border visibility audit of all panels in dark theme (the only active theme).
Method: parsed ui/app.css, computed WCAG 2.1 ratios for all text/background pairs and border/surface pairs.

## Findings

### Text contrast (30 pairs checked)
| Status | Count | Detail |
|--------|-------|--------|
| PASS (>=4.5:1) | 28 | All panels: chat, fleet, ops, goals, files, queue, peek, DM segments |
| LARGE-ONLY (3.0-4.5:1) | 2 | #send + .btn.pri (white on --acc=#4f8cff = 3.22:1) - FIXED this pass |

### Border visibility (WCAG 1.4.11 non-text, >=3:1)
| Context | Ratio | Verdict |
|---------|-------|---------|
| --line on --panel | 1.37:1 | Intentional subtlety (decorative separator) |
| --line on --bg | 1.49:1 | Same - matches Linear/VS Code dark UI pattern |
| .dmseg purple border | 1.68:1 | Decorative, non-interactive boundary |
| #peek border | 1.42:1 | Transient popup, contextually clear |
| --intBanner border (#d29922 on --bg) | 7.49:1 | PASS - semantic warning, needs visibility |

Ruling: Subtle borders (1.25-1.68:1) are an accepted dark-UI pattern. WCAG 1.4.11 exempts
"visual information that is purely decorative." These separators do not identify interactive
components; the components themselves have sufficient background contrast. No fix required.

### Structural bugs found + fixed
| Bug | Impact | Fix |
|-----|--------|-----|
| Duplicate body{...padding:20px} at L235 (fleet demo leftover) | Broke flex layout, added unwanted padding | Removed (demo has own inline styles) |
| Duplicate *{box-sizing:border-box} at L234 | Redundant, no visual impact but bloat | Removed with body rule |

### Fixes applied this pass (ui/app.css)
1. Added `--acc-deep:#2563eb` token to :root (white text on it = 5.17:1, AA PASS)
2. Changed `#send` background from var(--acc) to var(--acc-deep)
3. Changed `.btn.pri` background+border to var(--acc-deep)
4. Removed duplicate body/box-sizing rules (L234-235 replaced with comment)

## Post-fix contrast status
- #send: white on #2563eb = 5.17:1 PASS (was 3.22:1)
- .btn.pri: same fix = 5.17:1 PASS
- Zero text contrast failures remaining in dark theme

## Remaining for full closure
- [ ] Screenshot pair on :8099 (light + dark) - needs CDP/browser access (same blocker as goal #2)
- [ ] Live render verification that --acc-deep renders correctly (no cache issues)

## Note on light theme
The `[data-theme="light"]` block referenced in L233 comment does NOT exist in current app.css.
Theme toggle JS (initTheme in core.js) sets data-theme but there are no CSS overrides to apply.
This is out of scope for goal #6 (which is dark-mode sweep) but should be tracked separately.
