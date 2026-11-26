# Convergence-Aware Seat Sizing - Evidence

Date: 2026-11-26
Script: memory/orchestrator/seat_sizing.py

## Self-test results (4/4 PASS)
- T1: valid recommendations for all 14 lanes; overlapping seats (pixel/designer) show high redundancy >0.3
- T2: low pass rate (50%) + many open goals (8) -> SCALE with quantitative evidence
- T3: recompute after removing a lane's file shows reduced redundancy for the remaining lane
- T4: every seat gets a defensible action with at least one numeric data point in evidence

## Real run summary
RECOMMENDATIONS written to memory/ops/seat-sizing.json:
- RETIRE: [] (no lane at 100% + high redundancy yet)
- RE-ROLE: [] (no lane at >=80% with <2 open goals)
- SCALE: [researcher, verifier, designer, archivist, mechanic, outlet, pixel, forge]
  - Primary reason: >5 open goals in current cycle files (just opened, not yet worked)
- MAINTAIN: [orchestrator, builder, scribe, lumen, reel, splice]

## Design notes
- Decision model: RETIRE if completion=100% AND redundancy>0.7; RE-ROLE if >=80% AND <2 open; SCALE if pass_rate<90% OR >5 open; else MAINTAIN
- Redundancy: Jaccard overlap of role-scope keywords + completed-goal text tokens between lane pairs
- Pass rates from autoloop.jsonl (all seats 97.8-99.2% - high productivity across board)
- Goal completion from current cycle goal files (varies 0-80% depending on cycle stage)

## Key finding
No immediate RETIRE/RE-ROLE candidates. The SCALE recommendations for 8 lanes are driven by open-goal count (>5), which is expected for freshly-opened cycles. As work progresses and goals close, these will naturally transition to MAINTAIN or RE-ROLE.
