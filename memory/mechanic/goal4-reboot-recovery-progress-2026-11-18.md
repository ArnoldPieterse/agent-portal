# Goal #4 - Reboot-Recovery: Progress 2026-11-18

## What was done this pass
- Wrote `reboot_recovery_test.py` (5816 chars) - full simulated kill+restart test
  - Finds portal PID, kills it, waits up to 5 min for recovery
  - Logs to memory/mechanic/reboot-recovery.jsonl
  - Checks all 4 hosts post-recovery
  - Supports --dry-run mode (checks state without killing)

## Current state of acceptance criteria
| Criterion | Status |
|---|---|
| All 4 hosts pass dry-run | Pale+Black: port-verified PASS; White: sandbox-limited; Red: powered off |
| Simulated kill+restart <5 min | Script written, needs execution from White interactive session |
| Boot-detect schtask registered | NOT YET - command prepared below |

## Next step (requires White interactive session)
```
python reboot_recovery_test.py --dry-run   # verify state
python reboot_recovery_test.py             # live kill+restart test
```

## Schtask registration (run via elev.py on White)
```
schtasks /create /tn "RebootRecover" /tr "python C:\path\to\reboot_recover.py" /sc onstart /ru SYSTEM /rl HIGHEST /f
```

## Blocker
- Red .245 is powered off (all ports PERM_ERR since 11-16). Cannot verify until host is back.
- Sandbox cannot reach localhost:8099 or execute elevated commands.
