# FLEET ONE-PAGER - 2026-11-24

Source: **llm-judge-local** | planners: designer, builder, verifier | judge: local-rubric - winner C: judge seat unavailable - local rubric: grounding x4 + coverage x3 + day-fit bonus

## orchestrator
1. **Implement cycle_skeleton.py to auto-generate proposal skeletons at close** _(from: Open goal: Cycle Proposal Skeleton Generator)_ - Enables automated cycle planning
2. **Integrate skeleton generator into main dispatch loop** _(from: Open goal: Cycle Proposal Skeleton Generator)_ - Ensures proposals are created automatically

## researcher
1. **Execute Productivity Baseline Measurement script to capture current metrics** _(from: Queue #3: Productivity Baseline Measurement)_ - Establishes baseline for productivity tracking
2. **Analyze baseline data to identify initial efficiency bottlenecks** _(from: Queue #3: Productivity Baseline Measurement)_ - Informs future optimization strategies

## builder
1. **Modify agent_portal.py to inject idle tasks when fleet_mode is IDLE** _(from: Open goal: Idle Task Injector)_ - Prevents agent downtime during maintenance
2. **Implement memory/builder/fleet_mode_writer.py for atomic JSON writes** _(from: Open goal: fleet-mode.json Atomic Writer)_ - Ensures data integrity for mode state changes
3. **Add top-of-page banner in cockpit displaying current fleet mode** _(from: Open goal: Cockpit Mode Banner)_ - Provides visual status feedback to users

## verifier
1. **Write mode_transition_test.py to simulate fleet mode changes** _(from: Queue #1: Mode Transition Integration Test)_ - Validates transition logic correctness
2. **Create fleet-mode.json schema validator script** _(from: Queue #10: fleet-mode.json Schema Validator)_ - Ensures config file structural integrity

## designer
1. **Add ARIA-live region for mode changes in cockpit UI** _(from: Queue #4: Fleet Mode ARIA + Keyboard Nav)_ - Improves accessibility for screen readers
2. **Design CSS transition for mode background color shifts** _(from: Queue #9: Mode Transition Animation)_ - Enhances visual feedback during state changes

## archivist
1. **Archive daily snapshots of productivity-baseline.json to memory/archivist/** _(from: Open goal: Productivity Trend Archive)_ - Preserves historical data for trend analysis
2. **Log mode transition anomalies exceeding 30-min deviation** _(from: Open goal: Mode Transition Anomaly Log)_ - Tracks unexpected behavior for debugging

## scribe
1. **Generate structured Cycle Close-Out Report using cycle_closeout.py** _(from: Queue #7: Cycle Close-Out Report)_ - Documents cycle outcomes and metrics
2. **Write one-paragraph brief for each mode transition decision** _(from: Open goal: Mode Decision Brief)_ - Provides human-readable context for changes

## mechanic
1. **Implement memory/mechanic/fleet_mode_infra.py for low-level atomic writes** _(from: Queue #5: fleet-mode.json Atomic Writer (Infra))_ - Provides robust infrastructure for state management
2. **Create budget_monitor.py to read pass-budget.json every cycle** _(from: Open goal: Pass Budget Monitor)_ - Monitors resource usage against limits

_round stats: {"sig": "025b0a1a2da9", "date": "2026-11-24", "drafts": [{"label": "A", "agent": "designer", "model": "designer-q4", "stats": {"agents": 8, "items": 17, "grounded": 16, "ratio": 0.94, "missing": [], "repaired": false, "model": null}}, {"label": "B", "agent": "builder", "model": "Qwen3.8-27B-Q8_0", "_