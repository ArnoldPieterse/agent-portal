# FLEET ONE-PAGER - 2026-11-24

Source: **llm-judge-local** | planners: designer, builder, verifier | judge: local-rubric - winner A: judge seat unavailable - local rubric: grounding x4 + coverage x3 + day-fit bonus

## orchestrator
1. **Implement cycle_skeleton.py to auto-generate proposal JSON at close** _(from: Open Goal: Cycle Proposal Skeleton Generator)_ - Enables automated cycle planning
2. **Integrate skeleton generator into daily close-out hook** _(from: Queue #7: Cycle Proposal Skeleton Generator)_ - Ensures proposals are generated without manual trigger

## researcher
1. **Draft market prediction model for day 5-20 window** _(from: 30-Day Outcome: Predicting markets [day 5-20])_ - Prepares for 'Predicting markets' outcome
2. **Analyze current fleet data to baseline market signals** _(from: 30-Day Outcome: Predicting markets [day 5-20])_ - Provides input for prediction model

## builder
1. **Modify agent_portal.py to inject tasks when mode is IDLE** _(from: Queue #2: Idle Task Injector)_ - Activates idle productivity
2. **Add top-of-page banner in cockpit showing fleet mode color** _(from: Queue #10: Cockpit Mode Banner)_ - Provides visual status feedback
3. **Implement atomic write logic for fleet-mode.json** _(from: Open Goal: fleet-mode.json Atomic Writer)_ - Prevents corruption during mode switches

## verifier
1. **Write mode_transition_test.py to simulate fleet mode changes** _(from: Queue #1: Mode Transition Integration Test)_ - Validates transition integrity
2. **Create schema validator for fleet-mode.json structure** _(from: Queue #9: fleet-mode.json Schema Validator)_ - Ensures data consistency across agents

## designer
1. **Add ARIA-live region to announce mode changes to screen readers** _(from: Queue #3: Fleet Mode ARIA + Keyboard Nav)_ - Improves accessibility compliance
2. **Design CSS transition for background color shift on mode change** _(from: Queue #8: Mode Transition Animation)_ - Enhances user experience during transitions

## archivist
1. **Archive daily snapshot of productivity-baseline.json** _(from: Queue #5: Productivity Trend Archive)_ - Tracks long-term productivity trends
2. **Log mode transition anomalies exceeding 30-min deviation** _(from: Open Goal: Mode Transition Anomaly Log)_ - Identifies timing issues in fleet ops

## scribe
1. **Generate structured cycle close-out report via script** _(from: Queue #6: Cycle Close-Out Report)_ - Documents daily fleet performance
2. **Write one-paragraph brief for each mode transition decision** _(from: Open Goal: Mode Decision Brief)_ - Provides human-readable context for changes

## mechanic
1. **Implement low-level atomic writer for fleet-mode.json** _(from: Queue #4: fleet-mode.json Atomic Writer (Infra))_ - Provides infra support for builder's writer
2. **Measure wall-clock latency of mode transitions** _(from: Open Goal: Mode Transition Latency Measurer)_ - Identifies performance bottlenecks

_round stats: {"sig": "4922b78d8ad0", "date": "2026-11-24", "drafts": [{"label": "A", "agent": "designer", "model": "designer-q4", "stats": {"agents": 8, "items": 17, "grounded": 17, "ratio": 1.0, "missing": [], "repaired": true, "model": null}}, {"label": "B", "agent": "builder", "model": "Qwen3.8-27B-Q8_0", "st_