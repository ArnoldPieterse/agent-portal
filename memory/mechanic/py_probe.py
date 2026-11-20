import winrm
HOSTS = {'PALE': ('IP_PALE', 'pale'), 'BLACK': ('IP_BLACK', 'black'), 'RED': ('IP_RED', 'red')}
for host, (ip, user) in HOSTS.items():
    s = winrm.Session('http://' + ip + ':5985/wsman', auth=(user, ''), transport='ntlm',
                      operation_timeout_sec=60, read_timeout_sec=180)
    r = s.run_cmd('powershell', ['-NoProfile', '-Command',
        'Get-ChildItem -Path C:\\ -Filter python.exe -Recurse -Depth 3 -ErrorAction SilentlyContinue | Select-Object -First 5 -ExpandProperty FullName'])
    out = r.std_out.decode().strip()
    print(host, repr(out[:400]))
