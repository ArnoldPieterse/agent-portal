# Builder Assist: deploy_all_schtasks.py --dry-run mode
**Date:** 2026-11-23
**Assists:** Archivist goal 3 + Verifier goal 8 (both pending single White run)

## What was done
Added `--dry-run` flag to `memory/mechanic/deploy_all_schtasks.py`:
- Validates all 7 task script paths exist in the tree
- Prints PASS/MISSING per task with resolved relative path
- Safe to run from sandbox (no COM/schtasks calls)
- Catches mirror-clobber or rename regressions before the production run

## Verification
```
$ python memory/mechanic/deploy_all_schtasks.py --dry-run
  PASS: PortalLoadProbe           -> memory\ops\loadtest\register_daily_probe.bat
  PASS: MirrorHeal                -> memory\ops\mirror_heal.py
  PASS: BootRecoverDetect         -> memory\mechanic\boot_recovery_test.py
  PASS: LogRotateDaily            -> memory\mechanic\log_rotate.py
  PASS: ChaosDrillMonthly         -> memory\ops\chaos_drill.py
  PASS: ArchivistDecayWeekly      -> memory\archivist\decay_production.py
  PASS: VerifierSLO               -> memory\verifier\slo_check.py
ALL 7 tasks validated. Ready for production run on White.
```
`py_compile` passes clean.

## Also fixed
Updated `memory/archivist/decay-schtask-setup.md` to reference the correct task name
(ArchivistDecayWeekly, not ArchivistDecayScore) and script (decay_production.py, not
legacy decay_score.py --archive). Prevents confusion during White verification step.

## Impact
Reduces risk of the single White run: if any referenced file was clobbered/renamed by
mirror sync, `--dry-run` catches it pre-flight from sandbox without needing COM access.
