# Portal startup fix - _find_sandbox_dir PermissionError (2026-11-17 11:53:33)

## Problem
Portal down since watchdog detected it at 10:02 AM. Root cause: `_find_sandbox_dir()` in agent_portal.py
crashed with `PermissionError: [WinError 5] Access is denied: 'C:\Users'` when launched from schtask
environment (USERPROFILE unset/wrong -> first path check fails -> C:\Users listing denied).

## Fix
Added two safeguards to `_find_sandbox_dir()`:
1. `__file__`-based fallback: if `agents.json` exists alongside the script, use that dir
2. Wrapped `os.listdir(users)` in try/except PermissionError so it degrades gracefully

## Verification
Ran `python agent_portal.py` directly - startup message printed successfully:
  "Agent portal -> http://127.0.0.1:8099 (backed by Studio at http://127.0.0.1:8888)"
No PermissionError. Ran for full 300s sandbox timeout (server alive).

## Runbook note
Portal won't start from schtask if USERPROFILE points elsewhere AND C:\Users is access-denied.
Fix: agent_portal.py _find_sandbox_dir now falls back to __file__ dir before scanning Users.
