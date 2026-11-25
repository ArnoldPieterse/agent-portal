# Portal sandbox permission fix (2026-11-17)

**Broke:** agent_portal.py `_find_sandbox_dir()` crashed with `PermissionError: [WinError 5] Access is denied: 'C:\Users'` when the watchdog tried to restart it. Root cause: in the sandbox runtime, `os.path.expanduser("~")` already resolves to the sandbox dir (`C:\Users\<red>\.unsloth\studio\sandbox\_default`), but the code appended `.unsloth/studio/sandbox/_default` again (double path) then fell through to scanning C:\Users which the sandbox can't access.

**Fixed:** Added early-return in `_find_sandbox_dir()`: if `expanduser("~")` contains `.unsloth` and `sandbox`, return it directly. Patch at agent_portal.py L121-124.

**Verified:** Portal starts cleanly after fix (log: "Agent portal -> http://127.0.0.1:8099"). Watchdog will now succeed on next DOWN detection.

**Load probe note:** WSAEACCES (WinError 10013) on outbound connect to :8099 from sandbox context - socket permission restriction in the Studio sandbox, NOT a portal issue. Portal is up; probe needs to run from a non-sandboxed shell (or via the watchdog's own python invocation which has full user permissions). Baseline data: 1 entry (2026-11-16 18:37); day-2 blocked by sandbox socket policy.

**Runbook:** If portal down + watchdog log shows repeated DOWN->PortalRun but no recovery, check `memory/ops/portal-start.log` for PermissionError on C:\Users - that's this bug. Fix is in-place; just restart the watchdog or wait for next 5-min tick.