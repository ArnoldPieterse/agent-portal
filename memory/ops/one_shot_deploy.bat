@echo off
REM one_shot_deploy.bat - Single-action boot-recovery deployment for one fleet host.
REM Usage (on target host, via RDP or local console):
REM   1. Copy this file + boot_recovery.py + fleet_reload.py to C:\ops\ (or any dir)
REM   2. Double-click or run: one_shot_deploy.bat
REM Admin? -> registers ONSTART schtask. No admin? -> places VBS in Startup folder.
REM Idempotent: safe to re-run.
setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PY_EXE=pythonw.exe
set RECOVERY_SCRIPT=%SCRIPT_DIR%boot_recovery.py
set TASKNAME=FleetBootRecovery

echo === One-Shot Boot-Recovery Deploy: %COMPUTERNAME% ===
echo Date: %DATE% %TIME%
echo Script dir: %SCRIPT_DIR%

REM --- Step 1: Verify required files exist ---
if not exist "%RECOVERY_SCRIPT%" (
  echo [FAIL] boot_recovery.py not found in %SCRIPT_DIR%
  echo Copy it from the fleet repo (memory/ops/boot_recovery.py).
  goto :end_fail
)
if not exist "%SCRIPT_DIR%fleet_reload.py" (
  echo [WARN] fleet_reload.py not found. Recovery will fail at reload step.
)
echo [OK] Required scripts present.

REM --- Step 2: Try admin path (ONSTART schtask) ---
schtasks /query /tn "%TASKNAME%" >nul 2>&1
if %ERRORLEVEL%==0 (
  echo [INFO] Task [%TASKNAME%] already exists. Re-registering...
)
schtasks /delete /tn "%TASKNAME%" /f >nul 2>&1
schtasks /create /tn "%TASKNAME%" ^
  /tr "\"%PY_EXE%\" \"%RECOVERY_SCRIPT%\"" ^
  /sc onstart /ru SYSTEM /rl HIGHEST /f >nul 2>&1
if %ERRORLEVEL%==0 (
  echo [OK] ONSTART task registered (admin path).
  goto :step_verify
)

REM --- Step 3: Fallback - VBS in Startup folder (non-admin) ---
echo [INFO] Admin registration failed. Using VBS Startup fallback...
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
if not exist "%STARTUP_DIR%" mkdir "%STARTUP_DIR%"

REM Generate VBS with correct paths
> "%STARTUP_DIR%\boot_recovery.vbs" echo Set sh = CreateObject("WScript.Shell")
>> "%STARTUP_DIR%\boot_recovery.vbs" echo WScript.Sleep 180000 ' wait 3 min for network + Studio
>> "%STARTUP_DIR%\boot_recovery.vbs" echo sh.Run "\"%PY_EXE%\" \"%RECOVERY_SCRIPT%\" >> \"%SCRIPT_DIR%boot-recovery-log.jsonl\" 2>&1", 0, False

echo [OK] VBS placed in: %STARTUP_DIR%\boot_recovery.vbs
goto :step_verify

REM --- Step 4: Verification ---
:step_verify
echo.
echo === Running verification ===
python "%SCRIPT_DIR%verify_boot_deployment.py"
set VERIFY_RC=%ERRORLEVEL%
if %VERIFY_RC%==0 (
  echo.
  echo [PASS] Deployment verified on %COMPUTERNAME%. Boot-recovery is active.
  goto :end_ok
) else (
  echo.
  echo [WARN] Verification reported issues (RC=%VERIFY_RC%). Check output above.
)

goto :end_fail

:end_ok
endlocal
exit /b 0

:end_fail
endlocal
exit /b 1
