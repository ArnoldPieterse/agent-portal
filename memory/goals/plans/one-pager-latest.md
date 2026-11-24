# FLEET ONE-PAGER - 2026-11-24

Source: **llm-judge-local** | planners: designer, builder, verifier | judge: local-rubric - winner A: judge seat unavailable - local rubric: grounding x4 + coverage x3 + day-fit bonus

## orchestrator
1. **Implement cycle_skeleton.py to auto-generate proposal JSON at close** _(from: Open Goal: Cycle Proposal Skeleton Generator)_ - Enables automated cycle planning
2. **Integrate skeleton generator into daily 14:36 plan generation hook** _(from: 7-Day Plan: Generate daily social media posts [day 2-4])_ - Ensures next-day plan is drafted automatically

## researcher
1. **Draft market prediction data schema for day 5 scaffold** _(from: 7-Day Plan: Predicting markets [day 5-7])_ - Prepares input structure for Predicting markets
2. **Identify 3 open-source datasets for initial market model training** _(from: 7-Day Plan: day 6: first automated run of Predicting markets)_ - Provides data source for first automated run

## builder
1. **Implement fleet_mode_writer.py for atomic JSON writes** _(from: Queue #4: fleet-mode.json Atomic Writer (Infra))_ - Prevents corruption during mode transitions
2. **Add top-of-page cockpit banner showing current fleet mode** _(from: Queue #10: Cockpit Mode Banner)_ - Provides visual status indicator for operators
3. **Modify agent_portal.py to inject idle tasks in MAINTENANCE mode** _(from: Open Goal: Idle Task Injector)_ - Utilizes downtime for productivity

## verifier
1. **Write mode_transition_test.py simulating WORK->MAINTENANCE shift** _(from: Queue #1: Mode Transition Integration Test)_ - Validates state machine integrity
2. **Create fleet-mode.json schema validator script** _(from: Queue #9: fleet-mode.json Schema Validator)_ - Ensures config file validity before dispatch

## designer
1. **Add ARIA-live region for mode change announcements** _(from: Queue #3: Fleet Mode ARIA + Keyboard Nav)_ - Improves accessibility for screen readers
2. **Design CSS transition for background color shift on mode change** _(from: Queue #8: Mode Transition Animation)_ - Provides clear visual feedback to users

## archivist
1. **Archive daily snapshot of productivity-baseline.json** _(from: Open Goal: Productivity Trend Archive)_ - Tracks fleet efficiency trends over time
2. **Log mode transition anomalies exceeding 30-min deviation** _(from: Open Goal: Mode Transition Anomaly Log)_ - Flags scheduling drift for review

## scribe
1. **Generate one-paragraph brief for current mode decision** _(from: Open Goal: Mode Decision Brief)_ - Documents rationale for audit trail
2. **Write 10-line human-readable daily fleet state snapshot** _(from: Open Goal: Fleet State Snapshot (Daily))_ - Provides quick status overview for stakeholders

## mechanic
1. **Implement low-level atomic write utility in fleet_mode_infra.py** _(from: Queue #4: fleet-mode.json Atomic Writer (Infra))_ - Supports builder's atomic writer requirement
2. **Measure wall-clock latency for mode transition execution** _(from: Open Goal: Mode Transition Latency Measurer)_ - Identifies performance bottlenecks in state changes

_round stats: {"sig": "34fe823ddde8", "date": "2026-11-24", "drafts": [{"label": "A", "agent": "designer", "model": "designer-q4", "stats": {"agents": 8, "items": 17, "grounded": 17, "ratio": 1.0, "missing": [], "repaired": false, "model": null}}, {"label": "B", "agent": "builder", "model": "Qwen3.8-27B-Q8_0", "s_