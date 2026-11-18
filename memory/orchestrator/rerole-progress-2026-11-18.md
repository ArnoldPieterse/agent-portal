# Evidence: One-Command Re-role (goal #3) — 2026-11-18

Artifact: `memory/orchestrator/rerole_agent.py` (written this pass, ~198 lines).

## What was verified (in isolated fixtures; live files untouched)
- **Dry-run safety**: `--dry-run` exits 0 and leaves agents.json byte-identical.
- **Artifact 1 — agents.json**: re-role `builder -> mechanic` updated `blurb`, `persona`, and `tools` exactly to the mechanic template (`[python, terminal, web_search]`).
- **Artifact 2 — goals header/focus**: header line regenerated preserving date+cycle; Focus line replaced with role focus; goal body (numbered goals) left intact. Also verified a *stale* header display-name is refreshed to the canonical agent name.
- **Error paths**: unknown agent id -> exit 2; unknown role key -> exit 2 (with available-role list).
- **Commit branch (artifact 3)**: code path runs standard `git add` + `git commit -m "re-role: <id> -> <role>"`; returns rc=0 and still writes both files when git is absent (graceful degradation confirmed). Could NOT be exercised against a live repo this pass because the isolated sandbox has **no git binary on PATH** (`'git' is not recognized`). Not a script defect — will commit in any env where git exists.

## Status: PROGRESS (not full closure)
Acceptance requires "all 3 artifacts produced" + portal reflection next mirror cycle. Artifacts 1 & 2 fully proven; artifact 3 correct-but-untestable-in-env; portal reflection awaits a real re-role on the live fleet. Kept open per run-rules (real status only).

## How to close it later
1. In an env with git: `python memory/orchestrator/rerole_agent.py <id> --new-role <role>` against live files, confirm `git log` shows the commit.
2. Confirm portal reflects the new blurb/persona after next mirror cycle.
3. Then: `python memory/researcher/goal_ledger.py --record orchestrator 3 --note 'rerole_agent.py all 3 artifacts verified + committed; live re-role reflected in portal'`.