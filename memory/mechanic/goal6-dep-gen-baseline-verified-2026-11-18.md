# Goal #6 - Week-0 baseline created + diff verified against real reference

Date: 2026-11-18 ~08:4x UTC
Agent: Mechanic

## What was done
1. Created `memory/ops/schtask-snapshot-week0.json` — production baseline from documented task inventory (5 tasks, 4 edges). This is the reference for all future weekly diffs.
2. Verified end-to-end diff: ran `schtask_dep_gen.py --input week1-test.csv --prev-snapshot week0.json` → correctly emitted **ALERT NEW: TestCanaryTask** (6th task in test CSV).
3. Output written to `memory/ops/schtask-snapshot-week1-test.json` (6 tasks, 4 edges, diff.added=["TestCanaryTask"]).

## State for closure
- [x] Script built + unit-tested (2026-11-17)
- [x] Week-0 production baseline created (this pass)
- [x] One test task addition correctly flagged against real baseline (this pass)
- [ ] Two REAL weekly generations in production (needs schtasks /query on White — NEEDS-HUMAN, same COM blocker as goals #1/#2)

## Runbook note
When the first live `schtasks /query /fo CSV /v > snapshot.csv` runs on White, feed it to:
```
python memory/ops/schtask_dep_gen.py --input snapshot.csv --prev-snapshot memory/ops/schtask-snapshot-week0.json --output memory/ops/schtask-snapshot-week1.json
```
Subsequent weeks: chain `--prev-snapshot` to the prior week's output.
