# Goal #6: Scheduled-task dependency graph auto-generation built 2026-11-17

## What was done
Built `memory/ops/schtask_dep_gen.py` (3.2 KB) - parses schtasks /query CSV output,
infers dependency edges from known task names, and diffs against a previous snapshot
to flag NEW/REMOVED tasks.

## Test results (all PASS)
1. Parse: 5-task and 6-task CSVs correctly parsed
2. Diff: NewBackupTask correctly flagged as ADDED when appearing in week-2 snapshot
3. Diff: PortalDailyGitCommit/FleetProbe/RecoverAll correctly flagged as REMOVED
4. Edges: 4 dependency edges inferred (PortalRun -> GitCommit/FleetProbe/AgentChat, MirrorRun -> RemoteMemory)

## Remaining for closure
- Register weekly schtask on White (NEEDS-HUMAN: same COM/schtasks blocker as goal #1)
- Produce two real weekly generations with correct diff
- One test task addition correctly flagged in production

## Runbook note
Script is self-contained, no external deps beyond stdlib. Input = `schtasks /query /fo CSV /v > snapshot.csv`.
