# Evidence: Archivist Goal 1 - Autonomy Decay Detection (REACHED)
Date: 2026-11-25

## What was built
1. `memory/archivist/autonomy-decay-signals.md` - Full spec: 3 signals (S1 escalation rate, S2 rework rate, S3 intervention frequency), thresholds per signal, composite decay score formula, detection script spec with working code, current reading, limitations.
2. `memory/archivist/decay_detector.py` - Working detection script (verified runs, outputs JSON + human-readable).

## Verification
- Script executed successfully: `python memory/archivist/decay_detector.py --json` returns valid JSON with window_cycles [15,16,17], all 3 signals computed, composite score 0.967 (CRITICAL - expected due to small-N sensitivity documented in spec).
- All data sources cited exist on disk: human-interventions.jsonl (10 records), cycle-closeout.jsonl (9 records), autonomy-trend.jsonl (2 entries), intervention-graph.json (generated today).
- Thresholds are grounded in real baseline data from cycles 14-17.

## Acceptance criteria met
- [x] Define decay signals: S1 (escalation rate), S2 (rework rate), S3 (intervention frequency)
- [x] Per-agent escalation rate: tracked via intervention-graph.json per-agent counts
- [x] Rework rate: defined with proxy metric + proper fix path documented
- [x] Human-intervention frequency over rolling 3-cycle window: computed from real data
- [x] Output file: memory/archivist/autonomy-decay-signals.md with thresholds + detection script spec
