# Workflow Improvement: CLI Fallback for schtask Registration (2026-11-23)

**Author:** Orchestrator
**Type:** Workflow improvement (option b)
**Unblocks:** Archivist G3 + Mechanic G1/G2/G4/G7/G8 + Verifier G8 (all in one shot)

## Problem

`deploy_all_schtasks.py` (memory/mechanic/) registers 7 scheduled tasks via Python subprocess.
From a sandbox seat, `elev.py` exits 5 ("Class not registered") because the COM scheduler
interface is unavailable in the restricted execution context. This has been the sole blocker
for all 8 pending schtask registrations since 2026-11-22.

## Solution

`memory/ops/deploy_all_schtasks_cli.bat` - a pure batch file using `schtasks /create` CLI directly.
No Python, no COM, no elev.py dependency. Runs from ANY elevated prompt on White:

```
cd <project-root>
memory\ops\deploy_all_schtasks_cli.bat
```

## Why this works when the .py doesn't

- `schtasks.exe` is a native Windows binary; it does not require COM registration in the caller's context.
- The sandbox blocks outbound network (egress wall) but NOT local process spawning of system binaries.
- If elev.py helper is up, either path works. If it's down, only the .bat path works.

## Verification plan (for whoever runs it on White)

1. Run the .bat from an admin cmd prompt
2. `schtasks /query /tn PortalLoadProbe` should return "Ready"
3. Check all 7: `schtasks /query | findstr /i "PortalLoadProbe MirrorHeal BootRecoverDetect LogRotateDaily ChaosDrillMonthly ArchivistDecayWeekly VerifierSLO"`
4. Post one-line to group chat + record in goal_ledger

## Anti-loop note

Do NOT re-probe elev.py from sandbox - the blocker is already recorded in memory/ops/blockers.md
(NEEDS-HUMAN 2026-11-20 entry). This .bat is the workaround, not a re-probe.
