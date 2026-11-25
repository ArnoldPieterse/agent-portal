@echo off
cd /d C:\Projects\AgentPortal
echo === started %date% %time% === > fleet_reload_task.log
%USERPROFILE%\.unsloth\studio\unsloth_studio\Scripts\python.exe -u C:\Projects\AgentPortal\fleet_reload.py >> fleet_reload_task.log 2>&1
echo === exitcode %errorlevel% at %date% %time% === >> fleet_reload_task.log
