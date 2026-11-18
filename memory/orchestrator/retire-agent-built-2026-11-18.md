# retire_agent.py - BUILT + verified (2026-11-18)

Goal #4: Retirement Checklist Automation

## What was built
`memory/orchestrator/retire_agent.py` — one-command retirement checklist + executor.

## Usage
```
python memory/orchestrator/retire_agent.py <agent-id> --dry-run   # print checklist only
python memory/orchestrator/retire_agent.py <agent-id>            # confirm + execute
     [--agents-file PATH] [--memory-dir PATH] [--no-commit]
```

## Verified operations (fixture test, all PASS)
1. **Archive goals file**: `memory/goals/scribe.md` -> `memory/goals/archive/scribe-2026-11-18.md` ✅
2. **Rename agent memory dir**: `memory/scribe/` -> `memory/scribe_archived_2026-11-18/` ✅
3. **Remove agents.json entry**: 8 -> 7 agents, scribe absent ✅
4. **Strike INDEX lines**: `~~` prefix applied to matching lines in memory/INDEX.md + sub-indexes ✅
5. **TODO.md note appended**: retirement section with date + agent name ✅

## Error paths verified
- Unknown agent id -> exit 2 with known-ids list ✅
- Missing agents file -> exit 3 ✅
- Dry-run mode: prints full checklist (files, INDEX lines, references count), changes nothing ✅

## Scan results on live fleet (dry-run scribe)
- 2 files to archive (goals file + memory dir)
- 68 INDEX lines to strike across 5 index files
- 1258 references in other .md files (informational only, not auto-stripped)

## Remaining
- Live execution on a real agent (requires human confirmation - destructive)
- Git commit branch untestable in sandbox (no git binary)

(verified: 2026-11-18 - retire_agent.py written + tested on fixture: all 5 operations pass; dry-run on live scribe shows correct file list + INDEX line count)
