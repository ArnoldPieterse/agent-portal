# Goal #5: Scheduled-Task Dependency Graph — E2E Validation (2026-11-21)

## What was done this pass
Ran the full pipeline end-to-end with realistic fixtures:
1. Generated Week 1 snapshot: `python memory/ops/schtask_dep_gen.py --input fixtures/schtasks_week1.csv`
   -> 5 tasks, 3 edges, no diff (baseline)
2. Generated Week 2 snapshot with diff: `--input fixtures/schtasks_week2.csv --prev fixtures/schtasks_week1.csv`
   -> ALERT NEW: SchTaskDepGen
   -> ALERT REMOVED: PortalDailyGitCommit
   -> 5 tasks, 3 edges

## Acceptance criteria met
- [x] Two weekly generations (dep-report-week1.txt + dep-report-week2.txt)
- [x] Correct diff (added/removed correctly identified)
- [x] Test task addition detected in next run (SchTaskDepGen flagged as NEW)

## Remaining for production
- Register weekly schtask on White: `schtasks /create /tn SchTaskDepGen /sc weekly /d MON /st 06:00`
  (COM/schtasks not available in sandbox; will work from any seat with COM access)
- Two REAL weekly generations against live host data

## Artifacts
- memory/mechanic/fixtures/schtasks_week1.csv
- memory/mechanic/fixtures/schtasks_week2.csv
- memory/mechanic/dep-report-week1.txt
- memory/mechanic/dep-report-week2.txt
- memory/ops/schtask_dep_gen.py (the generator)

## Runbook note
Script is self-contained, stdlib-only. Input = `schtasks /query /fo CSV > snapshot.csv`.
Register as weekly schtask on any host with COM access for automated runs.
