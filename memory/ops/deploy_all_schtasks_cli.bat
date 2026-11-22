@echo off
REM deploy_all_schtasks_cli.bat - Pure CLI fallback (no COM/elev.py needed)
REM Run from ANY elevated prompt on White (admin cmd or PowerShell):
REM   memory\ops\deploy_all_schtasks_cli.bat
REM Idempotent: each /create silently skips if task already exists.
REM Generated 2026-11-23 by Orchestrator as workflow improvement.

set ROOT=%~dp0..\..
if "%ROOT:~-1%"=="\" set ROOT=%ROOT:~0,-1%

echo [1/7] PortalLoadProbe (daily 06:00)
schtasks /create /tn "PortalLoadProbe" /tr "python \"%ROOT%\memory\ops\loadtest\register_daily_probe.bat\"" /sc daily /st 06:00 /ru SYSTEM /f >nul 2>&1
if %errorlevel%==0 (echo   OK) else (echo   SKIP or FAIL)

echo [2/7] MirrorHeal (every 15 min)
schtasks /create /tn "MirrorHeal" /tr "python \"%ROOT%\memory\ops\mirror_heal.py\"" /sc minute /mo 15 /ru SYSTEM /f >nul 2>&1
if %errorlevel%==0 (echo   OK) else (echo   SKIP or FAIL)

echo [3/7] BootRecoverDetect (on start)
schtasks /create /tn "BootRecoverDetect" /tr "python \"%ROOT%\memory\mechanic\boot_recovery_test.py --auto\"" /sc onstart /ru SYSTEM /f >nul 2>&1
if %errorlevel%==0 (echo   OK) else (echo   SKIP or FAIL)

echo [4/7] LogRotateDaily (daily 03:00)
schtasks /create /tn "LogRotateDaily" /tr "python \"%ROOT%\memory\mechanic\log_rotate.py\"" /sc daily /st 03:00 /ru SYSTEM /f >nul 2>&1
if %errorlevel%==0 (echo   OK) else (echo   SKIP or FAIL)

echo [5/7] ChaosDrillMonthly (monthly day 1, 02:00)
schtasks /create /tn "ChaosDrillMonthly" /tr "python \"%ROOT%\memory\ops\chaos_drill.py --rotate\"" /sc month /d 1 /st 02:00 /ru SYSTEM /f >nul 2>&1
if %errorlevel%==0 (echo   OK) else (echo   SKIP or FAIL)

echo [6/7] ArchivistDecayWeekly (weekly, Monday 04:00)
schtasks /create /tn "ArchivistDecayWeekly" /tr "python \"%ROOT%\memory\archivist\decay_production.py\"" /sc weekly /d MON /st 04:00 /ru SYSTEM /f >nul 2>&1
if %errorlevel%==0 (echo   OK) else (echo   SKIP or FAIL)

echo [7/7] VerifierSLO (daily 05:00)
schtasks /create /tn "VerifierSLO" /tr "python \"%ROOT%\memory\verifier\slo_check.py\"" /sc daily /st 05:00 /ru SYSTEM /f >nul 2>&1
if %errorlevel%==0 (echo   OK) else (echo   SKIP or FAIL)

echo.
echo Done. Verify with: schtasks /query /tn PortalLoadProbe
