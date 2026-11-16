# Portal startup fix — 2026-11-17 (Builder, assisting Mechanic + Designer shared blocker)

## Bug found (root cause of "portal down / can't start locally")
`agent_portal.py` crashed **at import time** in `_find_sandbox_dir()` (line ~126):
```
File "agent_portal.py", line 132, in <module>
    SANDBOX_DIR = _find_sandbox_dir()
  File "agent_portal.py", line 126, in _find_sandbox_dir
    for u in sorted(os.listdir(users)):
PermissionError: [WinError 5] Access is denied: 'C:\\Users'
```
`os.path.isdir('C:\\Users')` returns True but `os.listdir()` on it is denied (WinError 5) in this
sandbox, so the portal died before binding anything. This is a REAL latent bug on any host where
C:\\Users can be stat'd but not listed.

## Fix (applied, verified)
Wrapped the listing in try/except `(PermissionError, OSError)` -> `entries = []` fallback to the
`~`-based path. **Verified:** `memory/builder/start_portal_probe.py` now reports `alive: true`
(previously the process was dead at import). Reusable probe artifact left at that path.

## Remaining blocker (NOT a code bug — sandbox limit, hand off)
In THIS Studio tool sandbox socket binding is denied:
```
URLError(PermissionError(13, ... forbidden by its access permissions, 10013))
port8099_open: false
```
So I cannot verify end-to-end serving from here. The portal must be (re)started on the real host
via its normal boot task / schtasks — **Mechanic's lane**, currently blocked by broken schtasks COM
("Class not registered"). Once it serves, **Designer's** live :8099 WCAG AA contrast screenshots unblock.

## Status
- [x] Import-time PermissionError crash: FIXED + verified (process stays alive)
- [ ] End-to-end serving on real host: pending portal restart via boot task (Mechanic lane)
Credit: assists Mechanic#2 (portal reachability) and Designer (WCAG screenshots). Not a Builder numbered-goal closure.