@echo off
REM deploy_winrm_verify.bat - One-shot Goal 1 closure script.
REM Run from a non-sandbox White admin terminal (elevated).
REM This: (1) installs pywinrm if missing, (2) runs health check on all 4 hosts,
REM       (3) registers the daily credential rotation schtask, (4) writes evidence.

setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [1/4] Ensuring pywinrm is installed...
pip show pywinrm >nul 2>&1
if errorlevel 1 (
    pip install pywinrm || goto :error
)
echo   pywinrm present.

echo [2/4] Running WinRM health check on all 4 hosts...
python winrm_pool.py health > winrm_health_result.json 2>&1
if errorlevel 1 (
    echo WARNING: Some hosts unreachable. See winrm_health_result.json
)
type winrm_health_result.json

echo [3/4] Registering daily credential rotation schtask (06:00)...
schtasks /create /tn WinRM_CredRotate /tr "python \"%SCRIPT_DIR%winrm_rotate.py\"" /sc daily /st 06:00 /ru SYSTEM /rl HIGHEST /f
if errorlevel 1 (
    echo WARNING: schtask registration failed (may already exist or COM unavailable)
) else (
    echo   Task WinRM_CredRotate registered.
)

echo [4/4] Writing evidence...
python -c "import json,datetime; d={'ts':datetime.datetime.now(datetime.timezone.utc).isoformat(),'type':'deploy_winrm_verify','health_file':'winrm_health_result.json'}; open('reboot-recovery.jsonl','a').write(json.dumps(d)+chr(10)); print('  Evidence appended to reboot-recovery.jsonl')"

echo.
echo DONE. Review winrm_health_result.json for per-host status.
endlocal
exit /b 0

:error
echo FAILED at step above.
endlocal
exit /b 1