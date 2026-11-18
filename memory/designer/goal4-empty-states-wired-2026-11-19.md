# Goal #4 Progress: Empty State Design wired (2026-11-19)

## What was done this pass
Wired the `UI.emptyState()` component (already in ui/icons.js) into all 3 remaining panels.

### Changes made:
1. **ui/app.css** (+7 lines): Added `.empty-state` CSS classes using design tokens:
   - `.empty-state` — flex column, centered, min-height 120px
   - `.empty-state-icon` — faint color, reduced opacity
   - `.empty-state-title` — fs-15 (h3 scale), dim color
   - `.empty-state-msg` — fs-14 (body scale), faint, max-width 280px
   - `.empty-state-cta` — fs-12 caption, br-sm radius

2. **ui/uploads.js** (goals panel + files panel):
   - Goals: `if(!o.agents||!o.agents.length)` → renders `UI.emptyState({icon:'goal', title:'No goals set', message:'Goal files in memory/goals/ will appear here with live progress rings.', ctaLabel:'Open TODO.md'})`
   - Files: `if(!files.length)` → renders `UI.emptyState({icon:'upload', title:'No uploads yet', message:'Drop files into the uploads/ folder on White, or use the + button below.', ctaLabel:'+ Upload'})`

3. **ui/core.js** (activity panel):
   - `if(!evts.length)` → renders `UI.emptyState({icon:'clock', title:'No activity yet', message:'Agent runs, tool calls, and memory operations will appear here as they happen.'})`

4. **index.html**: Added `<script src="ui/icons.js"></script>` before core.js
   - Pin advanced: 76e0188faaef → 1f3a18bccca4
   - Backup: memory/designer/index_html_CANONICAL_1f3a18bccca4_2026-11-19x.html

### Coverage (4 empty states for goal #4):
| Panel | State | CTA | Status |
|-------|-------|-----|--------|
| Fleet (#fleetPanel) | No agents online | — | ✅ (prior work, .fleet-empty) |
| Goals (#goalsPanel) | No goals set | Open TODO.md | ✅ this pass |
| Files (#filesPanel) | No uploads | + Upload | ✅ this pass |
| Activity (#actPanel) | No events | — | ✅ this pass |

### Remaining for full acceptance:
- [ ] Verify all 4 empty states render when API returns empty arrays (live test)
- [ ] Verify CTAs are clickable and functional
- [ ] CDP screenshot evidence (blocked - see memory/ops/blockers.md)

### Design decisions:
- Fleet panel keeps its existing `.fleet-empty` class (already styled, no migration needed)
- Activity panel has no CTA (no actionable next step when there's no history)
- All colors/sizes use tokens from ui/tokens.css — zero hard-coded values
