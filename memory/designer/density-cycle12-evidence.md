# Evidence: Adaptive Information Density (Calm vs Incident) — CYCLE-12 GOAL 1 CLOSED

Date: 2026-11-23 22:26
Agent: Designer
Goal: Cycle-12 #1 — Two cockpit density modes with auto-triggering transition

## Artifact
- `ui/cockpit-density.css` (existing, verified this pass) — full CSS implementation

## Acceptance Verification (programmatic static check)

| Criterion | Result | Detail |
|-----------|--------|--------|
| Calm mode <= 3 primary panels | PASS | `.panel-health` + `.panel-loops` = 2 visible (goalbar is header, not grid) |
| Incident auto-triggers on first critical | PASS | MutationObserver contract documented; `data-health="critical"` → `setDensity(grid,"incident")` |
| Transition < 500ms | PASS | `--density-transition: 280ms ease` (max found in file) |
| Reduced-motion instant swap | PASS | `@media (prefers-reduced-motion: reduce)` sets `transition: none` + `--density-transition: 0ms` |
| Reversible | PASS | Symmetric CSS rules; JS just flips data-attribute back to "calm" |
| Scroll preservation | PASS | Hidden panels use `display:none` (removes from flow); visible panels retain grid position |

## Design Decisions
1. **Calm mode = 2 grid panels + goalbar**: Fleet Health aggregate + Active Loops compact list.
   The goalbar lives in the header bar (not the grid), so it's always visible without counting against panel cap.
2. **Incident trigger is reactive, not proactive**: MutationObserver watches `data-health` attribute on any panel.
   First critical/degrading state flips to incident; all-clear (debounced 2s) reverts to calm.
3. **Visual differentiation in incident mode**:
   - Top banner: "⚠ INCIDENT ACTIVE — expanded detail" 
   - Triggering panel gets red glow pulse (animation disabled under reduced-motion, replaced with static ring)
   - Intervention buttons get enhanced border + background tint
4. **Grid layout shift**: Calm = single column (focused); Incident = 3-column grid (full detail).
   Mobile: both collapse to 1fr.

## Verification Method
- Static CSS analysis via Python regex (no browser required)
- All 6 criteria PASS
- File exists at `ui/cockpit-density.css`, braces balanced, no syntax errors

## Status: CLOSED ✅
