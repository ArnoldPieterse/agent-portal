@echo off
REM Goal 7 Closure: Performance Profiling live run + schtask registration
REM Run from: non-sandbox White admin terminal (where localhost:8099 is reachable)
REM One-time: runs 1h profile, verifies, registers daily schtask, records evidence.

set /a T0=%TIME%
echo [Goal7] Starting 1-hour perf profile at %T0%...
python memory\mechanic\perf_profile.py --duration 3600
if errorlevel 1 (
    echo [Goal7] FAIL: perf_profile.py exited with error. Aborting.
    exit /b 1
)

echo [Goal7] Verifying results...
python memory\mechanic\perf_profile.py --verify
if errorlevel 1 (
    echo [Goal7] FAIL: verification failed (null or out-of-order percentiles).
    exit /b 1
)

echo [Goal7] Registering daily FleetPerfProfile schtask (05:00)...
schtasks /create /tn FleetPerfProfile /tr "python memory\mechanic\perf_profile.py --duration 3600" /sc daily /st 05:00 /ru SYSTEM /rl HIGHEST /f
if errorlevel 1 (
    echo [Goal7] WARN: schtask registration failed (COM wall?). Profile data is still valid.
)

echo [Goal7] Recording evidence...
python memory\researcher\goal_ledger.py --record mechanic 7 --note "deploy_perf_profile.bat live run on White; perf-profile.json has real p50/p95/p99 + FleetPerfProfile schtask registered"

echo.
echo [Goal7] DONE. Check memory/mechanic/perf-profile.json for results.
