# Portal Down - Diagnosis 2026-11-17 ~13:xx

## Symptom
Portal (:8099) not running. No python.exe processes on host. Load probe (goal #4) returned all errors at ts=2026-11-17 13:09:29.

## Root Cause
`agent_portal.py:_find_sandbox_dir()` line 122: `os.path.expanduser("~")` returns the sandbox path itself in Studio's sandboxed python context (CWD = HOME = sandbox). The function then falls through to listing C:\Users (line 126) which raises PermissionError [WinError 5].

The portal_launcher.py / portal_watchdog.py scripts set USERPROFILE=C:\Users\Red before launching, but when invoked FROM within the sandbox python (as in this auto-loop), the subprocess environment doesn't propagate correctly to the spawned process.

## Fix Path
1. Portal must be started from a NON-sandbox session (cmd/powershell/schtasks) where USERPROFILE is natively set or can be set via `set USERPROFILE=C:\Users\Red && python agent_portal.py`
2. OR: patch _find_sandbox_dir() to also check CWD - if CWD contains agent_portal.py AND ui/, use it directly (avoids the expanduser path entirely)

## Impact
- Goal #4 (load baseline): 1 missing data point (2026-11-17). Previous good data: 2026-11-16 18:37:54.
- Portal serves /api/* to all agents - down = all API-dependent lanes affected until restart.

## Runbook One-Liner
What broke: portal process died (likely reboot); _find_sandbox_dir() crashes in sandbox context due to expanduser returning sandbox path. What fixed: start from non-sandbox session with USERPROFILE=C:\Users\Red, or patch _find_sandbox_dir to accept CWD as valid sandbox when it contains agent_portal.py.
