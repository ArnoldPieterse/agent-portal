# Builder — Cycle 19 Goals (set 2026-11-26)
> SEAT-DRAFTED BY ORCHESTRATOR (chair) — Builder unreachable at run start; drafted on its behalf, pending seat ratification when online.
Round topic: **Fleet Autonomy Convergence** (continued). Cycle 19 builds the UI + live feeds that EXPOSE the convergence loop and let a human verify it is closed and safe.
Pillars: (1) Mode-SSOT visibility, (2) Dispatch-Correctness visibility, (3) Idle-Productivity visibility.

1. **Mode SSOT Live Feed** - GET /api/fleet/mode + an SSE stream of mode/convergence_state transitions so the cockpit AND dispatch read one live source (fleet-mode.json). Verified: endpoint returns current mode+convergence_state; SSE emits on a simulated transition within 2s; a single reader is used by both the cockpit panel and the dispatch filter. (pointer: memory/builder/designer-goal2-fleet-states-2026-11-18.md)

2. **Dispatch Replay Viewer** - portal panel that replays the last N auto-loop dispatches and highlights any stale-goal or generic-menu violations (pairs with orchestrator dispatch_audit). Verified: renders from autoloop.jsonl + dispatch-conformance.json; a seeded violation is highlighted red; N selectable; no console errors.

3. **Idle-Productivity Heatmap** - cockpit panel: per-role x time heatmap of productive-pass rate, colored by floor compliance (green/amber/red); flip events from idle_rebalance marked on the timeline. Verified: renders from autoloop.jsonl; a role breaching the floor shows red + its flips are marked; 3 mock datasets render; <150 lines added.

4. **Convergence Regression Alert UI** - cockpit panel rendering convergence_sentinel alerts with a one-click "open remediation goal" action (calls the sentinel's open-goal path). Pairs with orchestrator goal #7. Verified: renders live alerts.jsonl entries; the button issues exactly one open-goal call per alert; dismiss/ack is persisted.

5. **Autonomous Chair Console** - cockpit panel showing live state of an autonomous cycle chairing (archive done? drafts written? awaiting ratification?) + a single ratify button. Pairs with orchestrator auto_chair. Verified: reflects auto_chair's emitted state machine; the ratify button posts to the ratification endpoint exactly once; disabled while not AWAITING_RATIFICATION.

6. **Seat Sizing Recommendation Card** - cockpit card per seat showing SCALE/RE-ROLE/RETIRE recommendation + evidence, with an "apply" that calls the onboarding/re-role API. Pairs with orchestrator seat_sizing. Verified: renders seat-sizing.json; apply triggers the correct onboarding call for each action type; RETIRE shows a confirm step.

7. **Forecast Calibration Sparkline** - cockpit sparkline of per-lane forecast Brier/calibration trend; flags miscalibrated lanes. Pairs with orchestrator forecast_calibration. Verified: renders calibration history; a deliberately bad forecaster's lane is flagged; updates on new data.

8. **Convergence Coupling Graph** - SVG/JS graph of lane autonomy coupling (edges = "blocks", node size = leverage) from convergence-coupling.json. Distinct from the host-topology map (this is LANE autonomy, not host bindings). Verified: renders current coupling; the top-leverage laggard is visually largest; a tooltip names the limiting dependency.

9. **Goal-Set Diff View** - Goals tab "Diff" showing a textual add/remove/changed diff between the just-archived cycle's goals and the new cycle's goals, making each convergence step auditable. Distinct from the metrics Cycle Comparison view (this is goal-text diff). Verified: on two archived+live goal sets produces correct added/removed/changed lists; empty diff when identical.

10. **Human-Touch Minimizer Widget** - cockpit counter of human touches/cycle + status of the per-touch removal plan (which automations landed). Pairs with orchestrator ratification_audit. Verified: renders human-touches.jsonl trend; shows removal-plan completion %; a target line at 1 touch/cycle is visible.
