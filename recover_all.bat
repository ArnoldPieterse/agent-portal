@echo off
cd /d C:\Projects\AgentPortal
echo === started %date% %time% === > recover_task.log
C:\Users\<white>\.unsloth\studio\unsloth_studio\Scripts\python.exe -u C:\Projects\AgentPortal\recover_all.py >> recover_task.log 2>&1
echo === exitcode %errorlevel% at %date% %time% === >> recover_task.log
