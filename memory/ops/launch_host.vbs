' PortalRun logon launcher (2026-11-23). Starts the single host process windowlessly.
' pythonw.exe in this build does not execute user code -> console python, window style 0.
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "C:\Projects\Workspace"
sh.Run """C:\Projects\Workspace\Python\pythoncore-3.15-64\python.exe"" ""C:\Projects\Workspace\portal_host.py""", 0, False
