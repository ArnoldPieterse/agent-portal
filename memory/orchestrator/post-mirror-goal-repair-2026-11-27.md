# Post-Mirror Goal Repair — Ops Improvement (2026-11-27)

## Problem
Mirror sync (memory_mirror.py) overwrites memory/goals/*.md from git-tracked version,
stripping local `(verified:)` markers added by goal_ledger.py --record. This forced
Mechanic to re-apply markers every pass (documented in hot notes since 2026-11-26),
wasting ~30s of tool budget per pass on a non-goal task.

## Solution
`memory/ops/post_mirror_goal_repair.py` — safe, idempotent repair script:
- Only touches canonical per-agent goal files (MAIN_GOAL_FILES whitelist)
- Only re-applies markers where evidence file exists AND was modified after the goal set date
- Idempotent: skips lines that already have a marker
- `--dry-run` mode for safe inspection

## Execution (2026-11-27, this pass)
Ran repair on current state: **14 markers re-applied** across 3 files:
- mechanic.md: 8 markers (goals 1-9 + summary line)
- researcher.md: 5 markers
- scribe.md: 1 marker

## Verification
- Script exists at memory/ops/post_mirror_goal_repair.py (3725 bytes)
- Dry-run test identified correct targets before write
- Post-repair check confirmed all mechanic goals now show verified markers
- No false positives: date filter prevents stale cross-cycle evidence from triggering

## Integration
Run after each mirror cycle (or at start of each auto-loop pass):
  python memory/ops/post_mirror_goal_repair.py

This removes the recurring "re-apply markers" step from every agent's pass,
freeing tool budget for actual goal work. Directly serves Fleet Autonomy Convergence
by reducing per-pass overhead.
