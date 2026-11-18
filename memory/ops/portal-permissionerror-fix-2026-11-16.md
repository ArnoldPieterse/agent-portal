# Portal down: _find_sandbox_dir PermissionError at import (2026-11-16)

Parent: memory/ops/INDEX.md. Sibling: windows-runbook.md (Portal lifecycle + restart trap).

## Symptom
Portal :8099 down; no pythonw/python.exe, no listener. `portal_run_err.log` traceback:
```
File "...sandbox\_default\agent_portal.py", line 65, in _find_sandbox_dir
    for u in sorted(os.listdir(users)):
PermissionError: [WinError 5] Access is denied: 'C:\\Users'
```
`SANDBOX_DIR = _find_sandbox_dir()` runs at import (module top) -> the process dies before it can bind :8099.

## Root cause
`_find_sandbox_dir()` fallback does `os.listdir('C:\\Users')`. When the portal user cannot enumerate
`C:\Users` (WinError 5), the exception propagates at import and kills the whole process. The function's
docstring says it exists to be robust across launch contexts - a hard crash defeats that.

## Fix (applied + compiles clean)
Wrapped the enumeration in `try/except OSError` -> on failure `entries=[]`, fall through to the existing
`return d`. Minimal, reversible. Guard is at agent_portal.py lines ~126-132 (`# Degrade, don't crash`).
Verified: Z:\agent_portal.py == C:\Users\Red\.unsloth\studio\sandbox\_default\agent_portal.py (same file, (other seat)
two views) - so the fix is in the exact copy the portal executes. `python -m py_compile` = OK.

## Current blocker for a DURABLE restart (environment, not code)
- Ad-hoc `pythonw agent_portal.py` / VBS `WshShell.Run` launches start fine and no longer crash, but are
  REAPED when the ephemeral tool session ends (known constraint - windows-runbook.md line 48). That is why
  the runbook mandates the scheduled-task launcher.
- `schtasks` is faulting on this host right now: `/query` -> exit 0xC0000004, `/run /tn PortalRun`
  -> "ERROR: Class not registered". So the canonical durable restart cannot be issued from my tools.

## One-line runbook note
BROKE: `_find_sandbox_dir()` `os.listdir('C:\Users')` raised WinError 5 at import, killing portal before :8099 bind.
FIXED: guarded the listdir with try/except OSError (degrade to existing fallback) - process no longer crashes at import.
REMAINING: durable restart needs `schtasks /run /tn PortalRun`; schtasks is currently broken ("Class not registered").
Auto-start safety net: PortalRun fires at logon, so next logon/reboot self-heals the portal with the fix in place.