# Designer Goal #2 — Fleet Panel States (Builder cross-assist)
Date: 2026-11-18
Owner: Designer (goal #2) | Contributor: Builder

## What was done
Added the three missing production states to `ui/fleet_topology.js` + CSS in `ui/app.css`:

1. **Loading state** — skeleton pulse shown while first `/api/fleet` fetch is in flight
2. **Error state** — visible warning banner with "showing cached data" when fetch fails (replaces silent fallback)
3. **Empty state** — graceful message + retry button when hosts array is empty
4. **Responsive SVG** — `width:100%; height:auto; max-width:960px` so it scales to container at 1024px and 1920px

## Files changed
- `ui/fleet_topology.js` (sha12=294aaca2ec20) — added showLoading/showError/showEmpty functions, empty-array guard in draw(), CSS class for responsive sizing
- `ui/app.css` (sha12=909533599016) — appended .ft-skel/.ft-loading/.ft-error/.ft-empty-state rules (all use design tokens, 0 hard-coded hex)

## Acceptance status
- [x] Loading state visible before data arrives
- [x] Error state shows on fetch failure with fallback data still rendered
- [x] Empty state handles hosts:[] gracefully
- [x] SVG scales responsively (viewBox + width:100%)
- [ ] Screenshots at 1024px/1920px as evidence (requires browser capture)

## Note
Bundle budget impact: app.css grew by ~415 bytes. Minified bundle needs re-measurement against 80KB target (was 79.9 KB pre-change).
