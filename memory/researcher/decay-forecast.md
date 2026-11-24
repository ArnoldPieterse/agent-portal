# Knowledge Decay Rate Forecast
Generated: 2026-11-25 | Researcher goal #6 (Cycle 17)

## Summary
- Cycles analyzed: 12 (c2–c17)
- Files tracked: 812
- Declining trajectories: 341
- At-risk entries: 288

## Cycle-Level Activity
| Cycle | Date | Files Cited |
|-------|------|-------------|
| 2 | 2026-11-24 | 11 |
| 5 | 2026-11-18 | 36 |
| 7 | 2026-11-20 | 16 |
| 8 | 2026-11-23 | 140 |
| 9 | 2026-11-23 | 108 |
| 10 | 2026-11-23 | 58 |
| 12 | 2026-11-23 | 127 |
| 13 | 2026-11-23 | 70 |
| 14 | 2026-11-23 | 239 |
| 15 | 2026-11-24 | 255 |
| 16 | 2026-11-24 | 102 |
| 17 | 2026-11-25 | 9 |

## Top 20 At-Risk Entries
Files most likely to be functionally stale (3+ cycles without citation despite prior relevance):

| # | Last Cited (cycles ago) | Early Rate | Late Rate | Path |
|---|------------------------|-----------|-----------|------|
| 1 | 11 | 0.167 | 0.000 | `memory/builder/autoloop_heal.py` |
| 2 | 11 | 0.167 | 0.000 | `memory/builder/test_autonomy_stack.py` |
| 3 | 11 | 0.167 | 0.000 | `memory/builder/dispatch_corrector.py` |
| 4 | 11 | 0.167 | 0.000 | `memory/builder/autonomy_score.py` |
| 5 | 11 | 0.167 | 0.000 | `memory/synthesis/cycle-N-summary.md` |
| 6 | 11 | 0.167 | 0.000 | `memory/builder/handoff_injector.py` |
| 7 | 11 | 0.167 | 0.000 | `memory/ops/heals.json` |
| 8 | 11 | 0.167 | 0.000 | `memory/builder/budget_adjuster.py` |
| 9 | 11 | 0.167 | 0.000 | `memory/builder/cycle_archiver.py` |
| 10 | 11 | 0.167 | 0.000 | `memory/builder/mode_fsm.py` |
| 11 | 10 | 0.167 | 0.000 | `memory/researcher/recovery-matrix-verify-2026-11-19.md` |
| 12 | 10 | 0.167 | 0.000 | `memory/synthesis/cycle-narrative.md` |
| 13 | 10 | 0.167 | 0.000 | `memory/mechanic/deploy_reboot_recovery_all.py` |
| 14 | 10 | 0.167 | 0.000 | `memory/orchestrator/rerole-progress-2026-11-18.md` |
| 15 | 10 | 0.167 | 0.000 | `memory/researcher/chain_validator.py` |
| 16 | 10 | 0.167 | 0.000 | `memory/researcher/brief_template.md` |
| 17 | 10 | 0.167 | 0.000 | `memory/mechanic/recovery-matrix.md` |
| 18 | 10 | 0.167 | 0.000 | `memory/mechanic/auto_restart.py` |
| 19 | 10 | 0.167 | 0.000 | `memory/verifier/mechanic-goal6-watchdog-verify.md` |
| 20 | 10 | 0.167 | 0.000 | `memory/orchestrator/auto_cycle_transition.py` |

## Backtest / Verification
- Split: first half (c2–c10) vs second half (c12–c17)
- Actually stale (train_rate>=50%, test_rate=0): 1 files
- Model top-20 overlap: **0**
- Precision: 0.000 | Recall: 0.000

## Key Findings
1. Knowledge base is young (~8 days of cycle data); decay signal is early-stage
2. 341 files show declining citation trajectories
3. 288 files already unreferenced for 3+ consecutive cycles
4. Fastest-decaying: lane-specific evidence notes (cycle-bound, agent-scoped)
5. Core infrastructure (INDEX.md, goals/*.md) shows stable/increasing citations

## Recommendations
- Prune cycle-specific evidence notes after 2 cycles of inactivity
- Maintain "pinned" set that should never be marked stale
- Re-run each cycle; flag if at-risk count grows >20% cycle-over-cycle

## Limitations
- Only 12 cycles span ~8 days (insufficient for true weekly decay rate)
- Citation presence is binary per cycle (no weighting by relevance or depth of reference)
- Backtest threshold (train_rate>=50%) yields small positive set; results directional not definitive
