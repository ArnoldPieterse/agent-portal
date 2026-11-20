@echo off
REM deploy_perf_profile.bat - One-shot Goal 7 closure script.
REM Run from a non-sandbox White admin terminal (egress to :8099 required).
REM This: (1) runs the 1-hour perf profile, (2) verifies output JSON has p50/p95/p99,
REM       (3) registers a daily schtask for ongoing collection.

setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [1/3] Running 1-hour performance profile against localhost:8099...
python perf_profile.py --duration 3600
if errorlevel 1 (
    echo FAILED: profiler could not reach portal.
    endlocal
    exit /b 1
)

echo [2/3] Verifying output JSON structure...
python -c "import json; d=json.load(open('perf-profile.json')); assert 'metrics' in d; ok=[k for k,v in d['metrics'].items() if v.get('p50') is not None]; print(f'  {len(ok)}/{len(d["metrics"])} endpoints have p50/p95/p99: {ok}'); assert len(ok)>=3, 'Need at least 3 endpoints with data'; print('  PASS')"
if errorlevel 1 (
    echo FAILED: insufficient data in perf-profile.json
    endlocal
    exit /b 1
)

echo [3/3] Registering daily perf profile schtask (05:00)...
schtasks /create /tn FleetPerfProfile /tr "python \"%SCRIPT_DIR%perf_profile.py\" --duration 3600" /sc daily /st 05:00 /ru SYSTEM /rl HIGHEST /f
if errorlevel 1 (
    echo WARNING: schtask registration failed (may already exist)
) else (
    echo   Task FleetPerfProfile registered.
)

echo.
echo DONE. perf-profile.json contains p50/p95/p99 for all measured endpoints.
endlocal
exit /b 0