' boot_recovery.vbs - Fallback for non-admin hosts.
' Place in: %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
' Waits 3 min post-boot (for network + Studio), then runs boot_recovery.py hidden.
Set sh = CreateObject("WScript.Shell")
WScript.Sleep 180000 ' 3 minutes for OS services + LM Studio to start
Dim scriptDir
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.Run "pythonw.exe " & Chr(34) & scriptDir & "\boot_recovery.py" & Chr(34), 0, False
