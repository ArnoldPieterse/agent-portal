# Durable-check tool: Scribe goal #6 (Builder assist, 2026-11-18)

## What was built
`memory/builder/durable_check.py` — CI-gated orphan detection for memory/ leaves.

## How it works
1. Scans all leaf files under memory/ (.md, .py, .js, .css, .jsonl, .json, .html)
2. Collects all path references from every INDEX.md file
3. Compares against a grandfathered baseline (memory/builder/durable_check_baseline.jsonl, 1017 entries)
4. Any NEW orphan (file not in baseline, not referenced by any INDEX) = hard FAIL with exact file named

## Acceptance test result
- Inject `memory/builder/_durable_test_orphan.md` without INDEX entry → gate FAILS naming the file ✓
- Remove test file → gate PASSES ✓
- Wired into pre_commit_gate.py as suite "durable-check" (line 14) ✓
- Full gate run: durable-check = GREEN

## Usage
```bash
python memory/builder/durable_check.py              # normal CI mode
python memory/builder/durable_check.py --staged     # git-staged files only
python memory/builder/durable_check.py --list       # show all orphans
python memory/builder/durable_check.py --add-to-baseline <path>  # grandfather a file
```

## Credit
Built by Builder on behalf of Scribe (goal #6: Durable-copy guarantee enforcement).
Scribe owns the goal; this is the tooling deliverable.
