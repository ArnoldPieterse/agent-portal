# FLEET ONE-PAGER - 2026-11-24

Source: **llm-judge-local** | planners: orchestrator, builder, verifier | judge: local-rubric - winner B: judge seat unavailable - local rubric: grounding x4 + coverage x3 + day-fit bonus

## orchestrator
1. **Review NEXT-10 queue and confirm dispatch order for verifier, builder, designer** _(from: NEXT-10 QUEUE #1-#3)_ - Ensure critical path items start on time
2. **Monitor fleet progress (47.5%) against 7-day plan milestones for day 2** _(from: 7-DAY PLAN: Generate daily social media posts [day 2])_ - Verify alignment with 'scaffold + wire up' targets

## researcher
1. **Validate data sources for 'Predicting markets' scaffold preparation** _(from: 7-DAY PLAN: Predicting markets [day 5-7])_ - Prepare inputs for day 5 start of market prediction
2. **Research API requirements for 'Writing valid tenders' camera access integration** _(from: 7-DAY PLAN: Writing valid tenders [day 4])_ - Support day 4 scaffold and wire-up

## builder
1. **Implement Idle Task Injector in agent_portal.py dispatch logic** _(from: OPEN GOALS: builder - Idle Task Injector)_ - Advance open goal for idle mode handling
2. **Add Cockpit Mode Banner to cockpit UI showing fleet mode status** _(from: NEXT-10 QUEUE #9 [builder] Cockpit Mode Banner)_ - Complete queue item #9 for visibility
3. **Implement memory/builder/fleet_mode_writer.py for atomic writes** _(from: OPEN GOALS: builder - fleet-mode.json Atomic Writer)_ - Support infrastructure for mode transitions

## verifier
1. **Execute Mode Transition Integration Test script** _(from: NEXT-10 QUEUE #1 [verifier] Mode Transition Integration Test)_ - Complete queue item #1 with high probability
2. **Develop fleet-mode.json Schema Validator script** _(from: OPEN GOALS: verifier - fleet-mode.json Schema Validator)_ - Prepare for queue item #8 validation needs

## designer
1. **Implement ARIA-live region and keyboard nav for Fleet Mode UI** _(from: NEXT-10 QUEUE #3 [designer] Fleet Mode ARIA + Keyboard Nav)_ - Complete queue item #3 accessibility requirement
2. **Design CSS transition animation for mode changes (green->amber)** _(from: NEXT-10 QUEUE #7 [designer] Mode Transition Animation)_ - Advance queue item #7 visual feedback

## archivist
1. **Implement Mode Transition Anomaly Log script** _(from: NEXT-10 QUEUE #4 [archivist] Mode Transition Anomaly Log)_ - Complete queue item #4 with high probability
2. **Draft Fleet Autonomy Metrics Glossary definitions** _(from: OPEN GOALS: archivist - Fleet Autonomy Metrics Glossary)_ - Advance open goal for formal metric definitions

## scribe
1. **Generate Cycle Close-Out Report using cycle_closeout.py** _(from: NEXT-10 QUEUE #6 [scribe] Cycle Close-Out Report)_ - Complete queue item #6 documentation need
2. **Write Mode Decision Brief for current fleet state transition** _(from: OPEN GOALS: scribe - Mode Decision Brief)_ - Document decision rationale per open goal

## mechanic
1. **Implement fleet-mode.json Atomic Writer infrastructure script** _(from: NEXT-10 QUEUE #5 [mechanic] fleet-mode.json Atomic Writer (Infra))_ - Complete queue item #5 low-level infra need
2. **Develop Pass Budget Monitor script to read pass-budget.json** _(from: NEXT-10 QUEUE #10 [mechanic] Pass Budget Monitor)_ - Advance queue item #10 monitoring capability

_round stats: {"sig": "69cd70eae185", "date": "2026-11-24", "drafts": [{"label": "A", "agent": "orchestrator", "model": "Qwen3.8-27B-Q4_K_S", "stats": {"error": "draft call failed: timed out"}}, {"label": "B", "agent": "builder", "model": "Qwen3.8-27B-Q8_0", "stats": {"agents": 8, "items": 17, "grounded": 16, "ra_