@echo off
setlocal enabledelayedexpansion
python memory/forge/canary_deploy.py memory/goals/next10.json White --dry-run >nul 2>&1
echo BLOCK_RC=!errorlevel!
python memory/forge/canary_deploy.py memory/goals/next10.json White --dry-run --skip-smoke --skip-perf --bypass-gate >nul 2>&1
echo BYPASS_RC=!errorlevel!
python memory/forge/dispatch_gate.py --selftest >nul 2>&1
echo SELFTEST_RC=!errorlevel!
endlocal
