# Goal #2 — deploy_startup_folder.py VBS generation fix
Date: 2026-11-17 (Mechanic)
Status: BUG FIXED + verified

## What was broken
`create_vbs()` in deploy_startup_folder.py used an f-string with embedded Python string-concat syntax
(`' + chr(39) + f'{python_exe}' + ...`). The generated VBS contained literal Python code instead of a
valid `sh.Run` call — would have failed at runtime on any host.

## Fix
Rewrote `create_vbs()` using `.format()` with proper VBS quote-doubling for the `sh.Run` argument.
Output now produces:
```
sh.Run """C:\path\python.exe" "C:\path\boot_recovery.py" >> "log.txt" 2>&1"", 0, False
```

## Verification
- Unit test: `create_vbs(delay_s=15, script_path=...)` returns VBS containing `sh.Run`, no Python artifacts.
- Full deploy blocked in sandbox (no %APPDATA%) — expected; will work on real hosts.

## Impact
Removes the last code blocker for the non-admin deployment path. Remaining: run on each host + cold-boot test.