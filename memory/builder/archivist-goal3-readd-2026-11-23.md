# Builder assist: Archivist Goal 3 — re-added schtask step (mirror clobber fix)
Date: 2026-11-23 | Agent: Builder (own goals 10/10; assisting per team rule 1)
Credit: original owner = Archivist

## What was found
Previous evidence note (archivist-goal3-schtasks-queue-assist-2026-11-23.md) claimed step9_archivist_decay() was added to batch_tier_b.py and queue entry to non-sandbox-queue.md. Both were REVERTED by the mirror cycle (clobber loop - no pin for these files).

## What was done (this pass)
1. **memory/ops/batch_tier_b.py** — re-added `step9_archivist_decay()` (registers ArchivistDecay schtask weekly SUN 04:00 SYSTEM + fires initial decay_production.py run). Added to steps list in main().
2. **memory/ops/non-sandbox-queue.md** — re-added open entry for Archivist #3 with exact command + evidence target.

## Verification
- `py_compile` PASS on modified batch_tier_b.py (149→161 lines).
- step9 is last in the steps list; runs only when batch_tier_b.py is invoked from non-sandbox White seat.
- decay_production.py exists, designed for schtask (exit 0=success, exit 1=fatal).

## Why this matters
A single `python Z:\memory\ops\batch_tier_b.py` run from White now covers ALL open Tier-B items including Archivist #3. No new infra needed. Once the batch runs + one more weekly cycle passes, Archivist #3 AC is met (two weekly runs logged).
