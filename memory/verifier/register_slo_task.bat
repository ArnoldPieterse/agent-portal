@echo off
REM Verifier Goal #2 - SLO scheduled task registration
REM Run from any non-sandbox (SYSTEM or admin) seat:
REM   cmd /c Z:\memory\verifier\register_slo_task.bat
schtasks /create /tn VerifierSLODaily /tr "cmd /c cd /d Z:\ \&\& python Z:\memory\verifier\slo_enforce.py" /sc daily /st 06:30 /f
if %errorlevel%==0 (
    echo REGISTERED: VerifierSLODaily at 06:30 daily
    schtasks /query /tn VerifierSLODaily /fo list
) else (
    echo FAILED: schtasks exit %%errorlevel%%
    exit /b 1
)
