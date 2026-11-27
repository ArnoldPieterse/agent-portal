# CSS Drift Fix: .readable Orphan (2026-11-26)

## Context
Forge's drift_detect.py caught `.readable` as an orphan selector in ui/app.css (line 480). No HTML/JS element referenced this class.

## Action
Removed the orphan rule + its comment (2 lines) from ui/app.css.

## Verification
`python memory/forge/drift_detect.py --json` -> status=CLEAN, css_drift=PASS, exit 0.

## Credit
Fix by Pixel; detection by Forge's gate pipeline (drift_detect.py Check 4).
