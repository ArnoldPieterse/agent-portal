@echo off
REM Daily load probe - registers schtask on White to run load_probe.py at 06:00 local
REM Run from White seat (non-sandbox or elevated): python elev.py --shell "memory\ops\loadtest\register_daily_probe.bat"
REM Or manually: schtasks /create /tn PortalLoadProbe /tr "python memory\ops\load_probe.py" /sc daily /st 06:00

echo Registering PortalLoadProbe daily task at 06:00...
schtasks /create /tn PortalLoadProbe /tr "python memory\ops\load_probe.py --host 127.0.0.1 --port 8099" /sc daily /st 06:00 /f
if %errorlevel%==0 (
    echo [OK] PortalLoadProbe registered. Will run daily at 06:00.
    echo Data appends to memory\ops\load-baseline.jsonl
) else (
    echo [FAIL] schtasks exit code %errorlevel%
)
pause