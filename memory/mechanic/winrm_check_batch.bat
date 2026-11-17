@echo off
REM WinRM verification for Pale + Black reboot-recovery legs
REM Run from White: cmd /c memory\mechanic\winrm_check_batch.bat
setlocal enabledelayedexpansion

set PALE_IP=IP_PALE
set BLACK_IP=IP_BLACK
set OUTFILE=%~dp0winrm_verify_result.json

> "%OUTFILE%" echo {
>> "%OUTFILE%" echo   "ts": "%date% %time%",
>> "%OUTFILE%" echo   "results": [

REM --- PALE ---
>> "%OUTFILE%" echo     {"host":"PALE",
for /f "usebackq delims=" %%a in (`powershell -NoProfile -Command "try { $c=New-Object System.Management.Automation.PSCredential('pale',(ConvertTo-SecureString '[REDACTED-CREDENTIAL]' -AsPlainText -Force)); $r=Invoke-Command -ComputerName %PALE_IP% -Credential $c -ScriptBlock { $reg=reg query 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' 2^>nul; if($reg -match 'Unsloth'){'OK'}else{'MISSING'} } -ErrorAction Stop; $r } catch {'ERR:'+$_.Exception.Message}"`) do (
>> "%OUTFILE%" echo       "hkcu_run":"%%a"
)

REM --- BLACK ---
>> "%OUTFILE%" echo     ,{"host":"BLACK",
for /f "usebackq delims=" %%b in (`powershell -NoProfile -Command "try { $c=New-Object System.Management.Automation.PSCredential('black',(ConvertTo-SecureString '[REDACTED-CREDENTIAL]' -AsPlainText -Force)); $r=Invoke-Command -ComputerName %BLACK_IP% -Credential $c -ScriptBlock { $reg=reg query 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run' 2^>nul; if($reg -match 'Unsloth'){'OK'}else{'MISSING'} } -ErrorAction Stop; $r } catch {'ERR:'+$_.Exception.Message}"`) do (
>> "%OUTFILE%" echo       "hkcu_run":"%%b"
)

>> "%OUTFILE%" echo   ]
>> "%OUTFILE%" echo }

echo Results written to %OUTFILE%
type "%OUTFILE%"
endlocal
