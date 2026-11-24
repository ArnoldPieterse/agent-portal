# FLEET ONE-PAGER - 2026-11-24

Source: **llm-judge-local** | planners: designer, builder, verifier | judge: local-rubric - winner A: judge seat unavailable - local rubric: grounding x4 + coverage x3 + day-fit bonus

## orchestrator
1. **Implement cycle_skeleton.py to auto-generate proposal skeletons at cycle close** _(from: Open Goal: Cycle Proposal Skeleton Generator)_ - Enables automated planning for next cycle
2. **Integrate skeleton generator into main orchestration loop** _(from: Open Goal: Cycle Proposal Skeleton Generator)_ - Ensures proposals are generated without manual trigger

## researcher
1. **Validate data sources for Predicting markets scaffold** _(from: 7-Day Plan: Predicting markets [day 5-7])_ - Prepares input pipeline for day 5 start
2. **Document market prediction baseline metrics** _(from: 30-Day Outcomes: Predicting markets)_ - Establishes reference for future verification

## builder
1. **Implement Idle Task Injector in agent_portal.py dispatch logic** _(from: Queue #2: Idle Task Injector)_ - Utilizes idle time during MAINTENANCE/IDLE modes
2. **Add Cockpit Mode Banner showing current fleet mode status** _(from: Queue #10: Cockpit Mode Banner)_ - Provides visual feedback for fleet state
3. **Implement fleet-mode.json atomic writer in memory/builder/** _(from: Open Goal: fleet-mode.json Atomic Writer)_ - Ensures safe concurrent writes to mode config

## verifier
1. **Write mode_transition_test.py to simulate fleet mode changes** _(from: Queue #1: Mode Transition Integration Test)_ - Validates integrity of mode switching logic
2. **Create fleet-mode.json schema validator script** _(from: Queue #9: fleet-mode.json Schema Validator)_ - Prevents invalid state configurations

## designer
1. **Add ARIA-live region for mode changes in cockpit UI** _(from: Queue #3: Fleet Mode ARIA + Keyboard Nav)_ - Ensures accessibility for screen readers
2. **Design CSS transition for mode background color shifts** _(from: Queue #8: Mode Transition Animation)_ - Provides smooth visual feedback on state change

## archivist
1. **Archive daily snapshots of productivity-baseline.json** _(from: Queue #5: Productivity Trend Archive)_ - Tracks performance trends over time
2. **Log mode transition anomalies to memory/archivist/** _(from: Open Goal: Mode Transition Anomaly Log)_ - Records deviations from forecast for analysis

## scribe
1. **Generate Mode Decision Brief summarizing current fleet state** _(from: Queue #6: Mode Decision Brief)_ - Provides human-readable context for decisions
2. **Create daily_snapshot.py for 10-line fleet state summary** _(from: Open Goal: Fleet State Snapshot (Daily))_ - Offers quick status overview without deep dive

## mechanic
1. **Implement low-level atomic writer in memory/mechanic/fleet_mode_infra.py** _(from: Queue #4: fleet-mode.json Atomic Writer (Infra))_ - Provides robust infrastructure for mode updates
2. **Build budget_monitor.py to read pass-budget.json every cycle** _(from: Open Goal: Pass Budget Monitor)_ - Monitors resource usage against limits

_round stats: {"sig": "ce06ca822b44", "date": "2026-11-24", "drafts": [{"label": "A", "agent": "designer", "model": "designer-q4", "stats": {"agents": 8, "items": 17, "grounded": 17, "ratio": 1.0, "missing": [], "repaired": true, "model": null}}, {"label": "B", "agent": "builder", "model": "Qwen3.8-27B-Q8_0", "st_