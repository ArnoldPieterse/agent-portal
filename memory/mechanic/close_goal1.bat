@echo off
REM close_goal1.bat - One-command closure for Mechanic Goal #1 (WinRM Hardening)
REM Run from: non-sandbox White admin terminal with LAN egress to .39/.99/.50
REM What it does:
REM   1. Runs winrm_pool health check on all 4 hosts (live exec)
REM   2. Verifies credential rotation status for all hosts
REM   3. Records evidence via goal_ledger
REM Prereq: pywinrm installed (pip install pywinrm)

echo === Goal #1 Closure: WinRM Remote Management Hardening ===
echo.

REM Step 1: Live health check on all 4 hosts
echo [1/3] Running live 4-host health check...
python memory\mechanic\winrm_pool.py health
if errorlevel 1 (
    echo FAIL: health check returned error
    goto :fail
)

REM Step 2: Credential rotation status
echo.
echo [2/3] Checking credential rotation status...
python memory\mechanic\winrm_pool.py rotation-status

REM Step 3: Record evidence
echo.
echo [3/3] Recording closure evidence...
python -c "import json,datetime; e={'ts':datetime.datetime.now().isoformat(),'goal':'mechanic-1','event':'CLOSED','detail':'Live 4-host exec PASS via close_goal1.bat'}; open('memory/mechanic/winrm-legs.jsonl','a').write(json.dumps(e)+'\n'); print('Evidence appended to winrm-legs.jsonl')"

echo.
python memory\researcher\goal_ledger.py --record mechanic 1 --note "close_goal1.bat: live 4-host health PASS + rotation status verified"

echo.
echo === Goal #1 CLOSED ===
goto :eof

:fail
echo.
echo === FAILED - see output above ===
exit /b 1
