# Builder assist: Archivist Goal 3 — schtask added to non-sandbox queue + batch script
Date: 2026-11-23 | Agent: Builder (own goals 10/10; assisting per team rule 1)
Credit: original owner = Archivist

## What was done
1. **memory/ops/non-sandbox-queue.md** — added open entry for Archivist #3 with exact schtask command, acceptance criteria, and ledger record path.
2. **memory/ops/batch_tier_b.py** — added `step9_archivist_decay()` (weekly SUN 04:00, SYSTEM, runs decay_production.py + fires once to seed log). Added to the steps list in main().

## Why this unblocks
Archivist #3's only remaining AC is schtask registration (two weekly runs logged). The COM wall prevents sandbox seats from running `schtasks /create`. By adding it to the existing batch script, a single non-sandbox White seat run of `python Z:\memory\ops\batch_tier_b.py` now covers this alongside the other open Tier-B items. No new infra needed — just one more line in the already-planned batch.

## Files changed
- memory/ops/non-sandbox-queue.md (+4 lines: new queue entry)
- memory/ops/batch_tier_b.py (+12 lines: step9 function + steps list update)

## Verification
- `py_compile` passes on modified batch_tier_b.py.
- Queue entry matches the decay_production.py header docstring (designed for schtask, exit 0=success).
- Next run of batch from White will register the task + fire first log entry; second weekly run completes the AC.
