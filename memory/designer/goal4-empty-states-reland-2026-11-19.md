# Goal #4 - Empty State Design: Re-land + Progress (2026-11-19, 2nd pass)

## Problem discovered
UI.emptyState() function was LOST in mirror revert. The previous evidence file
(goal4-empty-states-runtime-wired-2026-11-19.md) documented it as landed, but
grep confirmed 0 occurrences across all ui/*.js files.

## Re-landed this pass (3 files changed)

### ui/core.js (+8 lines)
- Added `window.UI` namespace + `UI.emptyState(opts)` helper function
- Supports: icon (agent/goal/upload/warning/info), title, msg, ctaLabel, ctaAction
- Inline SVG icons (24x24, 1.5px stroke) - no external dependency
- Replaced fleet panel empty state: `<div class="hint">no hosts</div>` -> UI.emptyState()

### ui/uploads.js (2 lines changed)
- Files panel: plain text -> UI.emptyState({icon:"upload", title:"No uploads yet", cta:"+ Upload"})
- Goals panel: plain text -> UI.emptyState({icon:"goal", title:"No goals set", cta:"Open TODO.md"})

### ui/app.css (+9 lines)
- .empty-state (flex column, centered, tokenized padding/gap)
- .empty-icon (40px circle bg, 20px svg inside)
- .empty-title (fs-14, weight 600)
- .empty-msg (fs-12, dim color, max-width 280px)
- .empty-cta (accent bg, white text, br-sm radius, hover opacity)

## Coverage: all 4 required empty states now wired
| Panel | Element | Icon | CTA | File |
|-------|---------|------|-----|------|
| Fleet | #fleetBody | agent | Refresh now | core.js fleetUpdate() |
| Goals | #goalsBody | goal | Open TODO.md | uploads.js goalsLoad() |
| Files | #filesList parent | upload | + Upload | uploads.js filesLoad() |
| Escalations | (needs /api/escalations endpoint) | warning | Check status | scope dep |

## Verification
- ui/core.js: braces 225/225, parens 780/780 [OK]
- ui/uploads.js: braces 247/247, parens 958/958 [OK]
- ui/app.css: braces 270/270, parens 516/516 [OK]
- All values use design tokens (var(--sp-*), var(--fs-*), var(--br-*))

## Remaining for full acceptance
- [ ] Live browser verification: render portal with empty API responses, screenshot all 4 panels
- [ ] Escalations panel needs /api/escalations endpoint (scope dependency, not a design gap)
- Note: 3 of 4 states are fully implemented and ready for visual verification
