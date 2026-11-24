# FLEET ONE-PAGER - 2026-11-24

Source: **llm-judge-local** | planners: designer, builder, verifier | judge: local-rubric - winner A: judge seat unavailable - local rubric: grounding x4 + coverage x3 + day-fit bonus

## orchestrator
1. **Review queue #1-#3 ETAs and confirm builder/verifier/designer capacity for tonight's mode transition work** _(from: NEXT-10 QUEUE #1, #2, #3)_ - Ensure critical path items start on time
2. **Verify fleet_mode.json is set to WORK before triggering next cycle dispatch** _(from: Open Goal: builder - Idle Task Injector)_ - Prevent idle task injection during active work

## researcher
1. **Draft data source list for 'Predicting markets' scaffold (day 5 start)** _(from: 7-Day Plan: Predicting markets [day 5-7])_ - Prepare inputs for day 5 scaffolding
2. **Identify API endpoints for 'Writing valid tenders' camera access requirement** _(from: 7-Day Plan: Writing valid tenders [day 4-7])_ - Support day 4 camera access goal

## builder
1. **Implement Idle Task Injector logic in agent_portal.py for MAINTENANCE/IDLE modes** _(from: Open Goal: builder - Idle Task Injector)_ - Enable autonomous idle work
2. **Add top-of-page Cockpit Mode Banner showing current fleet mode status** _(from: Open Goal: builder - Cockpit Mode Banner)_ - Provide visual feedback on mode state
3. **Write memory/builder/fleet_mode_writer.py for atomic fleet-mode.json updates** _(from: Open Goal: builder - fleet-mode.json Atomic Writer)_ - Ensure safe mode state persistence

## verifier
1. **Run Mode Transition Integration Test simulating WORK to MAINTENANCE switch** _(from: NEXT-10 QUEUE #1)_ - Validate transition logic before deployment
2. **Create fleet-mode.json Schema Validator script to check JSON structure** _(from: Open Goal: verifier - fleet-mode.json Schema Validator)_ - Prevent malformed mode state files

## designer
1. **Add ARIA-live region for mode changes in cockpit UI** _(from: Open Goal: designer - Fleet Mode ARIA + Keyboard Nav)_ - Ensure accessibility for screen readers
2. **Design CSS transition for mode background color shifts (green->amber)** _(from: Open Goal: designer - Mode Transition Animation)_ - Smooth visual feedback on mode change

## archivist
1. **Log any mode transition deviations >30min to anomaly log** _(from: Open Goal: archivist - Mode Transition Anomaly Log)_ - Track forecast accuracy for retro analysis
2. **Draft metrics-glossary.md defining fleet autonomy KPIs** _(from: Open Goal: archivist - Fleet Autonomy Metrics Glossary)_ - Standardize reporting terminology

## scribe
1. **Generate Cycle Close-Out Report for current cycle using cycle_closeout.py** _(from: NEXT-10 QUEUE #6)_ - Document cycle outcomes and efficiency
2. **Write one-paragraph brief explaining last mode transition decision** _(from: Open Goal: scribe - Mode Decision Brief)_ - Provide context for future audits

## mechanic
1. **Implement memory/mechanic/fleet_mode_infra.py for low-level atomic writes** _(from: NEXT-10 QUEUE #5)_ - Support builder's mode writer with infra layer
2. **Build Pass Budget Monitor to read pass-budget.json and alert on limits** _(from: Open Goal: mechanic - Pass Budget Monitor)_ - Enforce cycle resource constraints

_round stats: {"sig": "8360a2fe2964", "date": "2026-11-24", "drafts": [{"label": "A", "agent": "designer", "model": "designer-q4", "stats": {"agents": 8, "items": 17, "grounded": 16, "ratio": 0.94, "missing": [], "repaired": false, "model": null}}, {"label": "B", "agent": "builder", "model": "Qwen3.8-27B-Q8_0", "_