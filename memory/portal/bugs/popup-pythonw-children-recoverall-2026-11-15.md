# Bug: visible terminal popups return after reboot (2026-11-15) - pythonw children + RecoverAll
Status: FIXED + live-verified 2026-11-15 ~12:0x. User-critical complaint round 2 (round 1 = the four scheduled tasks, fixed earlier same day).

## Symptom
After the human rebooted all systems, `cmd`/`net` console windows reappeared on White's desktop although PortalRun/Mirror/Probe/DailyGit were already windowless.

## Root cause (two sources, both proven live)
1. **RecoverAll task** - the FIFTH boot-time launcher, missed by round-1 fix. Startup `_boot_recover.vbs` fires `schtasks /run /tn RecoverAll` at logon+3min; the task action was `recover_all.bat` DIRECTLY under an InteractiveToken, so Task Scheduler spawned a VISIBLE cmd for the whole ~6.5-min recovery run (today 11:19:23-11:25:55). It only fires at logon, which is why round-1 daytime verification saw nothing.
2. **pythonw child processes** - memory_mirror.py (`net use` on SMB reconnect, `git ls-files`) and agent_portal.py (`git` via /api/git + `_git`, python via `_run_index_check`) ran console children with plain `subprocess.run(capture_output=True)`. GUI parent (pythonw) + console child WITHOUT CREATE_NO_WINDOW = Windows allocates a fresh VISIBLE console per call. Round-1 verification at 10:57 missed it because the SMB connections were already alive that cycle (`os.stat` short-circuit -> no `net use`).

## Fix
- New `recover_hidden.vbs` (same pattern as `portal_hidden.vbs`: WshShell.Run style 0, bWaitOnCompletion=True so task Status stays Running); `schtasks /change /tn \RecoverAll /tr "wscript.exe ...\recover_hidden.vbs"` -> SUCCESS, XML verified.
- `creationflags=0x08000000` (CREATE_NO_WINDOW) on ALL subprocess.run sites: memory_mirror.py x3 (git ls-files, net use /delete, net use), agent_portal.py x3 (_git_allowlist, _run_index_check, _git). capture_output already pipes stdio, so nothing is lost.
- fleet_reload.py WHITE section (same audit): `_deferred_error` load responses (200 + active-generation deferral) now return 'deferred' instead of polling 25 min; DONE condition corrected to `Q8_0 resident OR len(ids)>=2` - the section only loads Q8 (Q4 is recover_all's job), so the old AND-condition guaranteed a TIMEOUT every boot (observed today 11:23-11:48, model actually loaded at 11:25).

## Verification (live)
- Portal restarted per RESTART TRAP: new PID 3496, CreationDate 11:57:30 > agent_portal.py mtime 11:56:40, /api/memory 200, _portal_pid.txt updated (it was STALE post-reboot: said 54008 while real listener was 4584 - trap step "read PID from file" must be cross-checked against the :8099 listener after any reboot).
- Forced the old popup path: `net use * /delete` (all 3 SMB drops), `schtasks /run /tn MemoryMirrorRun` -> net use re-ran for Red/Pale/Black + git ls-files; 75s continuous EnumWindows monitoring @300ms = ZERO visible ConsoleWindowClass windows; mirror run clean (2 pushed Red, 1290 unchanged, 0 errors).
- POST /api/git status under the new pythonw: zero visible consoles. Final desktop sweep: no ConsoleWindowClass windows at all.

## Rule (generalize)
Any script that runs under pythonw (or any GUI parent) MUST pass CREATE_NO_WINDOW to every console child, and any scheduled task whose action is a .bat under an interactive token WILL show a window - wrap it in a style-0 vbs. Verify popup fixes by FORCING the trigger path (drop connections / call the endpoint) while polling EnumWindows, never by checking after the fact.
