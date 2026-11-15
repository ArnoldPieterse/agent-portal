@echo off
rem =====================================================================
rem  portal_start.bat - Agent Portal (agent_portal.py) on http://127.0.0.1:8099
rem  Registered as schtask \PortalRun (interactive, runs this .bat).
rem    start/restart : schtasks /run /tn PortalRun
rem    health check  : curl http://127.0.0.1:8099/api/memory   -> HTTP 200 = up
rem  Logs (append)  : portal_run.log (stdout) / portal_run_err.log (stderr)
rem  Portal routes agent aliases quinn-q4 / atlas-q8 to Studio on :8888.
rem =====================================================================

cd /d C:\Projects\Workspace
rem pythonw = no console window (2026-11-15: visible cmd popups were critical user complaint)
"C:\Projects\Workspace\Python\pythoncore-3.15-64\pythonw.exe" agent_portal.py >> portal_run.log 2>> portal_run_err.log
