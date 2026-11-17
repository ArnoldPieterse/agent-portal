@echo off
setlocal enabledelayedexpansion
taskkill /f /im msedge.exe >nul 2>&1
set "EDGE=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
set "FX=file:///Z:/memory/designer/fleet-matrix.html"
set "OUT=Z:\memory\designer\breakpoint-evidence"
call :cap 768
call :cap 1024
call :cap 1920
echo ALL DONE
exit /b 0

:cap
set "W=%~1"
set "A=0"
:try
set /a A+=1
if !A! GTR 6 goto :failw
set "UD=Z:\memory\designer\_ud_%W%_!A!"
if exist "!UD!" rd /s /q "!UD!" >nul 2>&1
"%EDGE%" --headless --disable-gpu --no-sandbox --user-data-dir="!UD!" --hide-scrollbars --force-device-scale-factor=1 --window-size=%W%,800 --virtual-time-budget=6000 --screenshot="%OUT%\fleet-%W%px.png" "!FX!" >nul 2>&1
if not exist "%OUT%\fleet-%W%px.png" goto :try
for %%F in ("%OUT%\fleet-%W%px.png") do if %%~zF LEQ 2000 del "%OUT%\fleet-%W%px.png" >nul 2>&1
if not exist "%OUT%\fleet-%W%px.png" goto :try
echo [%W] OK attempt !A!
exit /b 0
:failw
echo [%W] FAILED after 6 attempts
exit /b 0