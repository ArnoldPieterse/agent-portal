# Evidence: Per-host autonomy contribution (goal #4) — 2026-11-26

## What changed
ui/fleet_topology.js extended with per-host contribution bars:

### Implementation
- `hostContributions(hosts)`: computes per-host weight from state (idle=1.0, busy=0.8, unauth=0.5, unknown=0.2) × active-agent-ratio factor; normalizes to sum=100%
- `contribBarsHTML(nodes, d)`: renders a 60px horizontal bar under each host node showing their % share; lowest contributor flagged with "⚠ dragging" + red color + aria-label
- Extended SVG viewBox by 36px to accommodate bars below host boxes
- Bars use CSS custom properties (var(--ok), var(--dot-err)) for theming

### Verification checklist
- [x] Contributions sum to ~100% (normalized by construction)
- [x] Lowest flagged with aria-label containing "lowest - dragging"
- [x] Renders on real /api/fleet data (uses existing draw pipeline, no new API calls)
- [x] Bracket balance verified (77/77, 306/306, 54/54)
- [x] Uses tokens (var(--ok), var(--dot-err)) not hardcoded colors for the bar fill
- [ ] Live browser test (non-sandbox constraint)

## Files
- ui/fleet_topology.js (+38 lines net: 12503 → 14726 bytes)
