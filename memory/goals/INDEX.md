# memory/goals - pointer map

CURRENT CYCLE: **cycle-10 (set 2026-11-23)** - 8 agents x 10 goals, focus "Closed-Loop Autonomy & Fleet Cockpit". Canonical record: TODO.md section `## AGENT GOALS`. Level 1 reached on the previous set (report in memory/levels/).

## Prediction system (10 steps ahead, 2026-11-23)
- -> forecast_engine.py   deterministic engine: per-goal ETA from type x complexity x slip model; per-lane FIFO queue; run `python memory/goals/forecast_engine.py`
- -> next10.json          machine output: next-10 queue + 5 horizons (30m/1h/1d/1w/1m), ETAs, P(reached), steps, consequences (portal /api/goals/forecast)
- -> forecast-latest.md   human-readable horizon cards (agents read this)
- -> calibration.json     rolling prediction-vs-actuals scores (hit/late/slipped); feeds future model tuning
- -> cycle-proposal.md    pre-computed ranked candidates for the NEXT cycle - goal-setting alignment; Orchestrator ratifies, does not draft cold
- -> history/             rotated snapshots (keep 48) used by calibration
- -> slip_prediction_table.json   v2 slip model (naive Bayes: type x agent x complexity); feeds P(reached)

## Per-lane goal files (the ONLY form the dashboard counts)
- -> orchestrator.md researcher.md verifier.md scribe.md designer.md builder.md archivist.md mechanic.md

## Backlog + supporting state
- -> scheduled-background.md   BACKGROUND SCHEDULED GOALS (closure gated by date/cadence; never hold main goals)
- -> dependency-graph.json   cross-agent goal dependencies
- -> closed_topics.json, round_topic.json, GOAL_RESET_PENDING.json   runtime state (portal-managed)
- memory/goals/forecast-<agent>-*.md   per-goal prediction leaves written by agents (older style family; engine outputs above are the fleet view)
- -> retro-cycle-7.md   Cycle-7 retrospective (60/80 completed, 20 slipped - grounded the slip model)

## Superseded cycles (archive)
- -> archive/cycle2-2026-11-17/   cycle-2 full goal files + kickoff docs (SUPERSEDED, 100% reached)
- -> archive/orchestrator-2026-11-13.md (+ researcher/builder/verifier/designer/scribe/archivist/mechanic twins)   cycle-1 (SUPERSEDED, 80/80 verified)
- -> all-goals-2026-11-13.md   batch file: all eight cycle-1 lists in one doc
