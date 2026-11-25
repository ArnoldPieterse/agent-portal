# Pixel — Convergence Metric Drill-Down View (goal #2) — structural verification
Run: 2026-11-25 · seat White (local, egress-walled; no JS runtime → source-level audit)

Method: static analysis of `ui/cockpit-convergence.js` verifying all acceptance criteria for the focus-trapped drill-down overlay.
Result: **26/26 checks pass**.

## Checks
- [x] LINEAGE entry for ckconv-gauge (Autonomy Score)
- [x] LINEAGE entry for ckconv-trend (Cycle Duration)
- [x] LINEAGE entry for ckconv-interventions (Human Interventions)
- [x] LINEAGE entry for ckconv-progress (Steady-State Progress)
- [x] trapFocus handles Tab key (forward)
- [x] trapFocus handles Shift+Tab (backward)
- [x] trapFocus wraps to first on forward past last
- [x] trapFocus wraps to last on backward past first
- [x] ESC key triggers closeDrillDown
- [x] closeDrillDown removes overlay from DOM
- [x] closeDrillDown restores focus to trigger element
- [x] Backdrop click closes (e.target === overlay)
- [x] Overlay uses position:fixed (no layout shift on open)
- [x] Overlay z-index:9999 (above all content)
- [x] role=dialog on overlay container
- [x] aria-modal=true set
- [x] aria-labelledby points to title heading
- [x] Close button has descriptive aria-label
- [x] Cards get role=button for AT semantics
- [x] Cards get tabindex=0 for keyboard access
- [x] Enter key opens drill-down (keyboard activation)
- [x] Space key opens drill-down (keyboard activation)
- [x] Source step in lineage display
- [x] Transform step in lineage display
- [x] Value step shows live metric value
- [x] bindDrillDown() called after each render (cards re-bound)

## Acceptance mapping
- **All 4 metrics open correct drill-down**: LINEAGE dict maps each data-testid to its title + source/transform/value steps; currentMetricValue() pulls live value from state.data.
- **Tab cycle stays trapped**: trapFocus intercepts Tab/Shift+Tab, wraps first↔last within the dialog's focusable elements (only the close button in v1).
- **ESC closes**: keydown handler on overlay checks for Escape → closeDrillDown().
- **No layout shift on open**: position:fixed inset:0 overlay does not participate in document flow; underlying grid unchanged.

Live CDP leg (real browser interaction) deferred to non-sandbox seat — recorded, not faked.
