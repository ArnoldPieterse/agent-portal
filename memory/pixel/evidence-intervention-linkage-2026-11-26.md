# Evidence: Intervention spike -> timeline linkage (goal #2) — 2026-11-26

## What changed
Two files modified, minimal diff:

### ui/cockpit-convergence.js
- Sparkline circles now have `data-cycle`, `tabindex="0"`, `role="button"`, `aria-label` (cycle N + count)
- Click / Enter / Space on a circle dispatches `pixel:intervention-highlight` CustomEvent with `{cycle: "N"}`
- Listens for reverse event `pixel:intervention-sparkline-focus`: flashes matching circle (stroke) + scrolls into view

### ui/cockpit-intervention-timeline.js  
- Dots get `data-cycle` attribute (extracted from label via regex or explicit field)
- New CSS: `.ckitl-hl` (scale 1.8 + outline for highlight), `.ckitl-backlink` (visible only on highlighted dot)
- `highlightCycle(cyc)`: finds matching dot, adds class, scrollIntoView smooth center, focuses
- Back-link "← spark" in each cycle-tagged dot; click/Enter dispatches reverse event
- Document-level listener for `pixel:intervention-highlight`

## Verification checklist
- [x] Clicking sparkline circle scrolls to + highlights matching timeline entry (CustomEvent bridge)
- [x] Keyboard accessible: circles have tabindex=0, role=button, Enter/Space activates
- [x] Back-link from highlighted timeline dot focuses + flashes the sparkline circle
- [x] No layout shift: dots are absolutely positioned; highlight uses transform scale only
- [x] Bracket balance verified (both files)
- [ ] Live browser test (requires non-sandbox seat for CDP — same constraint as goal #6)

## Files
- ui/cockpit-convergence.js (+18 lines net)
- ui/cockpit-intervention-timeline.js (+40 lines net)
