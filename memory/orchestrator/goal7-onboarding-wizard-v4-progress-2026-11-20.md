# Goal 7: Fleet Onboarding Wizard v4 — Interactive CLI (progress 2026-11-20)

## What was built this pass

Extended `onboard_agent.py` with a full interactive wizard mode (`--interactive` / `-i`):

1. **Interactive prompts** for all 4 fields:
   - Name (text input)
   - Role template (numbered menu from TEMPLATES dict + "custom" free-text option)
   - Model preference (catalog from MODEL_CATALOG with size/VRAM/ctx descriptions)
   - Tools subset (toggle-by-number, 'a' = all, Enter = accept default)

2. **`--tools` CLI flag** for non-interactive tool override (comma-separated).

3. **MODEL_CATALOG constant** mapping alias -> human-readable spec (from memory/llm/instances.md).

## Verification (all PASS this pass)

| Test | Command | Result |
|------|---------|--------|
| Compile | `compile(open('onboard_agent.py').read(), ...)` | PASS |
| Help shows new flags | `python onboard_agent.py --help` | Shows `--interactive`, `--tools` |
| Interactive dry-run (full wizard) | `io.StringIO('Sentinel\n1\natlas-q8\ny\n')` piped to main() | EXIT 0, all 3 artifacts produced |
| Non-interactive regression | `--name TestAgent --role researcher --dry-run` | EXIT 0, correct profile |
| Tools override | `--name MinimalBot --role builder --tools python,terminal --dry-run` | tools=[python, terminal] in output |

## Real round-trip executed 2026-11-20 ~08:45 (PASS)

**Onboard** `python memory/orchestrator/onboard_agent.py --name RosterProbe --role generic --model atlas-q8 --tools python --no-commit`:
- agents.json: added 'rosterprobe' (8 -> 9) — entry verified on disk (id/name/model_id=atlas-q8/tools=[python]/persona/blurb all present)
- memory/rosterprobe/INDEX.md created (127 B)
- memory/goals/rosterprobe.md skeleton created
- INDEX line added in memory/INDEX.md

**Retire** `echo yes | python memory/orchestrator/retire_agent.py rosterprobe --no-commit`:
- goals/rosterprobe.md -> ../goals/archive/rosterprobe-2026-11-20.md
- memory/rosterprobe -> memory/rosterprobe_archived_2026-11-20
- agents.json: removed (9 -> 8, json-grep hits = 0)
- INDEX line struck (~~...~~), TODO.md retirement note appended (line 552)

**Orphan check**: `agents.json` 0 rosterprobe refs; INDEX.md line struck not deleted; goal file archived; dir renamed. CLEAN.

Note: retire_agent.py requires interactive yes/no confirm — pipe `echo yes |` in non-tty runs.

## Closure
- [x] Real onboarding of test agent, all files verified on disk
- [x] Retired via retire_agent.py, no orphaned refs
- [x] Ledger record (goal_ledger.py --record orchestrator 7, 2026-11-20)

ACCEPTANCE MET: full onboarding produces all artifacts; retire is clean.

## Files changed
- `onboard_agent.py` (+91 lines: MODEL_CATALOG, ALL_TOOLS, interactive_prompt(), main() modifications)
