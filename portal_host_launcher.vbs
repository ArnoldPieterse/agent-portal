' portal_host_launcher.vbs - windowless one-shot launcher for the consolidated host script.
' Runs from the Startup folder at logon (no UAC, no console window).
' portal_host.py is self-supervising with a pid-file single-instance guard, so
' duplicate launches exit immediately.
Set sh = CreateObject("WScript.Shell")
sh.Run "C:\Projects\AgentPortal\Python\pythoncore-3.15-64\python.exe C:\Projects\AgentPortal\portal_host.py", 0, False
