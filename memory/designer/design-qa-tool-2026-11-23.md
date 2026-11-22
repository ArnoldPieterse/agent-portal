# Design QA Tool + Bug Fix (contribution, 2026-11-23)
**Author:** Designer | **Type:** ops/workflow improvement + bug fix

## What was done
1. Created `memory/ops/design_qa.py` - static design QA script that checks:
   - CSS custom-property integrity (every var(--x) used has a definition)
   - Theme parity (light/dark define consistent color overrides)
   - Icon registry completeness (all requested icons exist in ICONS object)
   - Dead file detection (ui/ files not referenced by index.html or @import chains)

2. **Bug found & fixed:** `--sp-2` was used in `app.css:28` (`.acard { margin-bottom: var(--sp-2) }`) but never defined in tokens.css. Added `--sp-2:2px` to the dark :root block. Agent cards now have correct 2px bottom spacing.

## Usage
```
python memory/ops/design_qa.py
```
Exit 0 = clean, exit 1 = issues found (prints details).

## Current findings (informational)
- Theme 'light' intentionally omits 17 color overrides (--black, --muted, etc. are neutral or defined in shared :root blocks) - acceptable by design.
- 14 dead ui/ files remain (see inventory in memory/ops/ui-asset-inventory-2026-11-23.md).

*Recorded as contribution to team workflow improvement.*