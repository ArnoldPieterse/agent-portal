@echo off
REM fleet_schtask_register.bat - Mechanic 2026-11-17
REM Run as Administrator on each host. Registers scheduled tasks for Goal #2 + #4.
REM Usage: run the section matching your hostname, or all sections (idempotent).

setlocal
set FLEET_ROOT=C:\Users\%USERNAME%\fleet
set PY=python

REM ============================================================
REM HOST DETECTION
REM ============================================================
for /f "tokens=1" %%i in ('hostname') do set MYHOST=%%i
echo Registering fleet tasks on: %MYHOST%

REM ============================================================
REM GOAL #2: FleetBootRecovery (all 4 hosts)
REM Fires at logon + every 5 min; boot_recovery.py checks uptime < 5min before acting
REM ============================================================
schtasks /create /tn "FleetBootRecovery" /tr "\"%PY%\" \"%FLEET_ROOT%\memory\ops\boot_recovery.py\"" /sc minute /mo 5 /ru %USERNAME% /rl limited /f >nul 2>&1
echo   FleetBootRecovery: %errorlevel% (0=OK)

REM ============================================================
REM GOAL #4: LoadProbeDaily (White only - where portal lives)
REM Fires daily at 09:00; runs load_probe.py against local :8099
REM ============================================================
if /i "%MYHOST%"=="WHITE" (
    schtasks /create /tn "LoadProbeDaily" /tr "\"%PY%\" \"%FLEET_ROOT%\memory\ops\load_probe.py\" --host 127.0.0.1 --port 8099" /sc daily /st 09:00 /ru %USERNAME% /rl limited /f >nul 2>&1
    echo   LoadProbeDaily: %errorlevel% (0=OK)
) else (
    echo   LoadProbeDaily: skipped (not White)
)

REM ============================================================
REM VERIFY
REM ============================================================
echo.
echo --- Registered tasks on %MYHOST% ---
schtasks /query /tn "FleetBootRecovery" /fo list 2>nul | findstr /i "TaskName Status"
schtasks /query /tn "LoadProbeDaily" /fo list 2>nul | findstr /i "TaskName Status"

echo Done.
endlocal