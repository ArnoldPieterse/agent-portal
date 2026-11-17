# Goal #6 - two-week generation + diff pipeline proven end-to-end (2026-11-18)

Date: 2026-11-18 ~08:09 UTC
Agent: Mechanic (Red sandbox)
Goal: #6 Scheduled-task dependency graph productionization

## What was done (NEW this pass - not re-probing the schtasks wall)
Built `memory/ops/schtask_dep_twoweek_harness.py` (124 lines) on top of the
existing `schtask_dep_gen.py` (no new machinery). It exercises the FULL weekly
generation + diff flow end-to-end and writes dated baseline artifacts:
  - memory/mechanic/dep-snapshots/week-1.csv      (6-task fleet fixture)
  - memory/mechanic/dep-snapshots/week-1-graph.json
  - memory/mechanic/dep-snapshots/week-2.csv      (week-1 + 1 added test task)
  - memory/mechanic/dep-snapshots/week-2-graph.json  (diff vs week-1)
  - memory/mechanic/dep-snapshots/twoweek-diff-report.json

## Verification (harness exit 0, all checks PASS)
- week-1 task_count == 6; week-2 task_count == 7
- week-1 has >=4 inferred dependency edges
- EXACTLY ONE task ADDED in diff = \\TestTaskAddition (the planted test task)
- NOTHING removed week1->week2
- ALERT NEW emitted to stderr naming the added task
Evidence: memory/mechanic/goal6-dep-gen-twoweek-evidence.jsonl (verdict PASS)

## Why this does NOT re-probe the blocker
Prior synthetic tests proved parse/diff/alert on ad-hoc fixtures. This pass
proves the DATED two-week cadence as a real pipeline producing baseline files -
the exact closure criterion "two weekly generations with correct diff; one test
task addition correctly flagged". Uses a deterministic fixture as stand-in for
the real snapshot, so no live schtasks COM session is needed.

## Remaining for full closure (still the known wall)
- Run the identical two-week flow on REAL `schtasks /query` CSVs captured from
  White non-sandbox seat (week 1 + week 2, 7 days apart) -> production cadence.
The pipeline is now proven; only real-data capture remains.

## Runbook note
What broke: goal #6 had only ad-hoc synthetic proof, no end-to-end two-week
cadence. What fixed it: schtask_dep_twoweek_harness.py drives schtask_dep_gen.py
across two dated fixtures and asserts the diff flags exactly the planted test task.
