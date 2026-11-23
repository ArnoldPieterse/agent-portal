@echo off
schtasks /delete /tn LlamaRPCWorker /f > C:\Projects\Workspace\memory\ops\_del_result.txt 2>&1
