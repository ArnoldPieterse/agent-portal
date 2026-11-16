@echo off
REM boot_recovery_register.bat - Register boot_recovery.py as ONSTART scheduled task.
REM Run on each fleet host (requires admin). Idempotent: deletes existing task first.
REM Usage: boot_recovery_register.bat [task_name]
REM   Default task name: FleetBootRecovery

setlocal
set TASKNAME=%~1
if "%TASKNAME%"=="" set TASKNAME=FleetBootRecovery

set SCRIPT_DIR=%~dp0
set PY_EXE=pythonw.exe
set RECOVERY_SCRIPT=%SCRIPT_DIR%boot_recovery.py

echo Registering [%TASKNAME%] -> %RECOVERY_SCRIPT%

REM Delete existing task (ignore error if not present)
schtasks /delete /tn "%TASKNAME%" /f >nul 2>&1

REM Create ONSTART task: runs at system startup, no user session needed.
REM /sc onstart = trigger at OS boot (not logon).
REM /ru SYSTEM = run as Local System (no interactive session required).
schtasks /create /tn "%TASKNAME%" ^
  /tr "\"%PY_EXE%\" \"%RECOVERY_SCRIPT%\"" ^
  /sc onstart /ru SYSTEM /rl HIGHEST /f

if %ERRORLEVEL%==0 (
  echo [OK] Task [%TASKNAME%] registered (ONSTART, SYSTEM).
  echo Verify: schtasks /query /tn "%TASKNAME%" /v /fo list | findstr "TaskName\|Status\|Trigger"
) else (
  echo [FAIL] Could not register task. Error code %ERRORLEVEL%.
  echo Fallback: copy boot_recovery.vbs to %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
)

endlocal

REM --- VBS fallback (no admin needed, per-host) ---
REM If schtasks fails (non-admin), use this instead:
REM   Save as boot_recovery.vbs in the user's Startup folder.
REM Content (see below):
REM   Set sh = CreateObject("WScript.Shell")
REM   WScript.Sleep 180000 ' wait 3 min for network + Studio
REM   sh.Run "pythonw.exe " & WScript.ScriptFullName & "..\boot_recovery.py", 0, False
