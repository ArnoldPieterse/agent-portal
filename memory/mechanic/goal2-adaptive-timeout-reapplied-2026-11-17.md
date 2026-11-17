# Goal #2: Adaptive Timeout Re-applied (2026-11-17)

Parent: memory/goals/mechanic.md. Sibling: goal2-boot-recovery-adaptive-wiring-2026-11-17.md.

## What ran
`_adaptive_timeout()` re-implemented in `memory/ops/boot_recovery.py` (previous edit was lost/reverted).
Updated `wait_studio()` signature from `timeout_min=5` to `timeout_s=300` (seconds-based, adaptive).

## Test results
15/15 PASS (`boot_recovery_test.py`), including new test_adaptive_timeout():
- No history -> 300s fallback: PASS
- Synthetic log (gaps of 120s) -> 180s computed (1.5x): PASS
- adaptive_timeout event logged with samples count: PASS
- Full flow sequence correct when no history exists: PASS

## What this unblocks
Boot recovery will now self-tune its wait window per host after accumulating boot data.
First boot on a fresh host uses 300s default; subsequent boots adapt to observed timing.

## Remaining for Goal #2 closure
- [ ] Deploy ONSTART task on Pale/Black/Red (admin or VBS fallback)
- [ ] One real cold-boot per remote with timestamped evidence
- [ ] Red .245 powered off — leg stays open until host returns