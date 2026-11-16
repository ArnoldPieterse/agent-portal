# Portal DOWN 2026-11-16 — crash cause + durable fix (Mechanic)

**One-line runbook note:** Portal :8099 was down because `_find_sandbox_dir()` crashed at startup with `PermissionError [WinError 5]` listing `C:\Users` (USERPROFILE unset/wrong in the pythonw launch context forced the fall-through scan); fixed by anchoring on the file's own location + making the user-profile scan PermissionError-safe. Restore = run `schtasks /run /tn PortalRun` from a real White host session (or wait for next-boot recover_all) — schtasks/direct-spawn are blocked inside the agent sandbox, so Mechanic could not bring it up live from here.

## Evidence
- **Symptom:** no :8099 listener, no portal pythonw process (socket probe code 10013; psutil showed only probe processes). `_portal_pid.txt` = 21284 (STALE — that PID is dead).
- **Crash cause** (`portal_run_err.log`, last traceback):
  ```
  File ".../agent_portal.py", line 74, in _find_sandbox_dir
      for u in sorted(os.listdir(users)):
  PermissionError: [WinError 5] Access is denied: 'C:\Users'
  ```
  Root cause: `os.path.expanduser("~")` resolved to a wrong home (USERPROFILE unset/wrong), so the primary `~/.unsloth/...` check missed and it fell into the `C:\Users\*` scan, which the process is not permitted to list.
- **Fix applied** (`agent_portal.py`, `_find_sandbox_dir()`): (1) new most-reliable anchor — if `HERE` itself is `.../.unsloth/studio/sandbox/_default`, return it; (2) wrapped `os.listdir(users)` in `try/except OSError` so a permission denial can never crash startup. Docstring made raw (`r"""`) to avoid `\U` escape SyntaxError.
- **Verified on disk:** `py_compile` = OK; function returns `C:\Users\Red\.unsloth\studio\sandbox\_default` (isdir=True) under BOTH wrong-USERPROFILE and no-USERPROFILE, with NO exception raised.
- **Still open (live restore):** :8099 not yet re-bound — sandbox blocks `schtasks` (COM "Class not registered") and direct `subprocess.Popen` of the portal (unsafe-code guard). Unblock step: `schtasks /run /tn PortalRun` from a real White session, or next boot (recover_all.py step 6 auto-starts portal if down).
