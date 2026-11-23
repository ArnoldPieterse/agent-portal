# Spec: Adaptive Information Density (Calm vs Incident)
Date: 2026-11-23 | Lane: Designer | Cycle-12 Goal #1

## Artifacts
- ui/cockpit-density.css — mode styles (calm/incident), transitions, reduced-motion
- ui/cockpit-density.js — DensityController: MutationObserver auto-trigger + scroll preservation
- memory/designer/cockpit-density-spec-2026-11-23.md — this spec

## Design Rationale
Calm mode reduces cognitive load during normal operation by collapsing the cockpit to
the 3 highest-value panels (health, autonomy loop, goal bar). The operator gets a
single-glance "all good" signal without scanning 6+ panels.

Incident mode is an emergency expansion: when any panel enters critical/degrading state,
ALL panels become visible and the triggering panel gets a pulsing red border so the
operator's eye goes directly to the problem. The transition is fast (<500ms) because
in an incident context every second of latency matters.

## Acceptance Criteria Verification
| Criterion | How met |
|-----------|---------|
| Calm mode shows <= 3 primary panels | CSS: .cd-calm hides hosts/agents/decisions/topology; only health+autonomy remain visible (2 panels + goal bar in header) |
| Incident auto-triggers on first critical | JS: MutationObserver watches data-health attr; 'critical' or 'degrading' triggers mode switch |
| Transition < 500ms, reversible | CSS: 300ms opacity+transform transitions; controller.setMode() is bidirectional |
| Preserves scroll on non-critical panels | JS: snapshotScroll + restoreScroll on mode change for all .ckp__panel elements |
| Reduced-motion = instant swap | CSS: @media (prefers-reduced-motion: reduce) sets transition:none on all density transitions |

## Integration Notes
- Add `data-health="ok|warn|critical|degrading"` to each `.ckp__panel` element
- Include cockpit-density.css after cockpit-responsive.css
- Include cockpit-density.js after cockpit-density.css (needs DOM ready)
- Call DensityController.init() on page load; it auto-detects the .ckp container
- Manual override: DensityController.setMode('incident') from any JS context
