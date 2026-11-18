# Goal #4 - Boot-detect schtask registration added to batch_tier_b.py

Date: 2026-11-18 (auto-loop pass)
Agent: Mechanic (Red seat)

## What was done
- Added `RebootRecoveryDetect` schtask registration to batch_tier_b.py step4:
  - `/sc onstart /delay PT5M /ru SYSTEM` — fires 5 min after any boot
  - Runs `reboot_recovery_test.py --dry-run` to verify all 4 hosts post-reboot
  - Logs result to reboot-recovery.jsonl (existing pipeline)
- Verified batch_tier_b.py compiles clean after edit.
- Re-ran dry-run from this seat: 2/4 PASS (Pale 21.5ms, Black 30.7ms); White+Red FAIL (expected sandbox limitations).

## State for closure
- Script + registration ready in batch_tier_b.py; needs ONE non-sandbox execution on White.
- After execution: schtask auto-fires on every future boot; evidence accumulates in reboot-recovery.jsonl.
- Full acceptance = all 4/4 PASS from White + one real kill+restart <5min recovery.

## Runbook note
boot-detect schtask (RebootRecoveryDetect) is now part of batch_tier_b.py step4. Execute `python batch_tier_b.py` from a non-sandbox White session to register it alongside the other 5 tasks.