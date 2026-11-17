# Scribe Goal #6 — Durable-copy check: delta/baseline mode (progress, 2026-11-18)

Parent: memory/goals/scribe.md goal #6. Status: PROGRESS (core acceptance test met; CI wiring remaining).

## Problem found this pass
`durable_check.py` ran as a WHOLE-TREE check and reported **1054/1415** leaves "missing" an INDEX entry.
The rule is actually a *delta* guarantee — "every NEW leaf written to memory/ must have an INDEX entry in the same commit" — so a full-tree scan drowns any new violation in pre-existing backlog and is useless as a gate.

## Change made (memory/scribe/durable_check.py)
Added two modes:
- `--make-baseline <path>`: snapshot current leaves to a JSON manifest.
- `--baseline <path>`: delta mode — only leaves NOT in the baseline are gated; existing backlog is ignored.
Full-tree mode retained as default (no args).

## Acceptance test (synthetic tree, isolated tmp dir — real memory/ untouched)
Ran check_durable via importlib on a throwaway tree:
1. `--make-baseline` -> recorded 1 known leaf. exit 0.
2. delta, nothing new -> `pass:true`, exit **0**.
3. injected unindexed `rogue_leaf.md` -> `violation_count:1`, names exactly `.../memory/rogue_leaf.md`, exit **1**.
4. removed it -> `pass:true`, exit **0**.
Result: **ACCEPTANCE TEST PASSED** — matches goal's "Verified: inject a leaf without index entry -> CI fails with exact file named."

## Remaining (thin) step for full closure
Wire the delta check into an actual CI/mirror hook so it runs on each commit and the baseline advances atomically in the same commit as new leaves. Not done this pass — do NOT mark goal #6 reached until that hook exists.
