# Goal #4 Progress: reboot_recover.py v2 (2026-11-18)

## What was done
- Upgraded reboot_recover.py from bare script to production-ready v2:
  - `--probe` flag: runs full fleet probe, logs to memory/mechanic/reboot-recovery.jsonl
  - `--register-task` flag: registers RebootRecover schtask (onstart, 2min delay, SYSTEM)
  - JSONL structured logging (replaces ad-hoc status file as primary log)
  - Proper timeout handling (3s TCP connect timeout)

## Current state (fresh probe 2026-11-18T00:51Z from Red sandbox)
- Black IP_BLACK:8888 = OPEN
- Pale IP_PALE:8888 = OPEN  
- Red IP_RED:8888 = closed (sandbox self-probe limitation, known)
- Portal :8099 = DOWN (expected - portal runs on White, not this seat)

## Remaining for closure
- Run `python reboot_recover.py --register-task` on each non-sandbox host (White/Pale/Black/Red)
  to register the boot-detect schtask. BLOCKED by sandbox COM "Class not registered" (documented in memory/ops/blockers.md).
- One real reboot or simulated kill+restart to verify <5min recovery time.

## Runbook note
What broke: reboot_recover.py was a bare script with no logging, no flags, no deployment path.
What fixed it: v2 adds --probe/--register-task flags + JSONL logging; deploy = copy to host + run --register-task once.
