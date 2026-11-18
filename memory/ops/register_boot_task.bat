@echo off
REM register_boot_task.bat - Register FleetBootRecovery ONSTART scheduled task.
REM Run as admin on each fleet host. Idempotent (overwrites existing).
REM No Python dependency - uses system schtasks directly.

set TASK_NAME=FleetBootRecovery
set SCRIPT_PATH=%~dp0boot_recovery.py

REM Find python.exe (prefer uv-managed, fall back to PATH)
where python >nul 2>&1
if %errorlevel%==0 (
    set PYTHON_CMD=python
) else (
    echo [ERROR] python not found on PATH. Aborting.
    exit /b 1
)

echo [%COMPUTERNAME%] Registering %TASK_NAME%...
echo   Script: %SCRIPT_PATH%
echo   Python: %PYTHON_CMD%

schtasks /create /tn "%TASK_NAME%" /tr "\"%PYTHON_CMD%\" \"%SCRIPT_PATH%\"" /sc onstart /ru SYSTEM /rl HIGHEST /f
if %errorlevel%==0 (
    echo   OK - task registered.
) else (
    echo   FAILED (need admin). Run this script elevated.
    exit /b 1
)

echo [%COMPUTERNAME%] Verifying...
schtasks /query /tn "%TASK_NAME%" /fo LIST | findstr /i "TaskName Status"
echo Done. %TASK_NAME% will fire on next system start.