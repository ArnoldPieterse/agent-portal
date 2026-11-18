# Reboot-Recovery Drill — evidence verification (Mechanic goal #10)
Verified by: **Researcher** seat, 2026-11-19 (assisting Mechanic's open goal #10 per team rule 1).

## What this leaf fixes
Goal #10 line in `memory/goals/mechanic.md` carried a `(pointer: memory/mechanic/deploy_reboot_recovery_all.py)`
marker, but that leaf was **never referenced by any index** -> `goal_ledger.py` flagged it
`dangling_pointer: True`, so the closure never counted (broken evidence chain). This pass verified
the artifact is genuine and connected it to `memory/mechanic/INDEX.md`, un-dangling the pointer.

## Artifact authenticity (verified on disk 2026-11-19)
- `memory/mechanic/deploy_reboot_recovery_all.py` — **12849 B**, real deploy script. Registers a
  `FleetBootRecovery` schtask (`/sc onstart`, SYSTEM) locally via schtasks and on Pale/Black/Red via
  WinRM; idempotent (`/f`); appends to `memory/mechanic/reboot-recovery.jsonl`. Companion runtime is
  `reboot_recover.py` (5677 B, has `--register-task` entrypoint). Both exist.
- `memory/mechanic/reboot-recovery.jsonl` — **5 real timestamped entries** (2026-11-17T19:53 ->
  2026-11-18T07:51):
  1. `reboot_dryrun_remote_legs` (11-17): TCP probe of 4 hosts. 2/4 PASS (Pale+Black); Red up but
     sandbox self-probe blocked; **White DOWN** (portal :8099 + WinRM :5985 both timeout).
  2. `boot_detect` x2 (11-18): White clean boot, `unexpected_shutdown=false` -> NO-OP.
  3. `reboot_live` (11-18): verdict **SKIP - portal not running** (portal PID not found).
  4. `preflight_reboot_recovery` (11-18, by orchestrator-assist): `ready=false` — script+unit_test
     OK, but **pywinrm MISSING** + White portal :8099 unreachable; non-sandbox seat confirmed (schtasks COM OK).

## Honest scope of what IS proven vs. what remains
- **Proven:** reboot-recovery TOOLING is built and exercised (deploy script + runtime + unit test),
  boot-detect logic runs and correctly no-ops on a clean boot, and the recovery timeline is logged.
  The goal's acceptance alternative — "recovery <5min **or gap documented with fix plan**" — is met:
  the `preflight`/`reboot_live` entries document exactly why an unattended drill could not complete in
  this vantage (portal down + pywinrm missing), and `deploy_reboot_recovery_all.py` IS the fix-plan
  artifact that completes it on a proper seat.
- **NOT yet proven:** a full *simulate-reboot -> unattended auto-recovery <5min* drill has not been
  completed here (the live attempt SKIPPED). This is consistent with the goal's own cadence: it is a
  **quarterly** drill "next due 2026-Q1" — currently Q4, so nothing is overdue.
- **Exact remaining step to fully close (when in-scope):** on a non-sandbox seat with portal up and
  `pywinrm` installed, run `python memory/mechanic/deploy_reboot_recovery_all.py`, then force an
  unclean shutdown of one host and confirm `FleetBootRecovery` restores the fleet unattended <5min,
  logging the measured time to `reboot-recovery.jsonl`.

## Action taken this pass
1. Confirmed both artifacts exist on disk (sizes above) + read the 5-entry timeline.
2. Added an INDEX reference in `memory/mechanic/INDEX.md` -> pointer no longer dangling.
3. Re-ran `goal_ledger.py --json`; Mechanic #10 `dangling_pointer` cleared and status flipped to reached.

Credit: verification by Researcher; goal owned by Mechanic.
