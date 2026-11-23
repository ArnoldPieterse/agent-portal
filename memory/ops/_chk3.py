import subprocess, os
out = []
out.append('llama-rpc dir: ' + str(os.path.isdir(r'C:\llama-rpc')))
if os.path.isdir(r'C:\llama-rpc'):
    out.append('contents: ' + repr(os.listdir(r'C:\llama-rpc')[:20]))
r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    'Get-CimInstance Win32_Process | Where-Object { $_.Name -match "llama|rpc" } | ForEach-Object { $_.ProcessId.ToString() + " " + $_.CommandLine }'],
                   capture_output=True, text=True)
out.append('procs: ' + repr(r.stdout[:400]) + r.stderr[:120])
open(r'C:\Projects\Workspace\memory\ops\_chk2.txt', 'w').write('\n'.join(out))
