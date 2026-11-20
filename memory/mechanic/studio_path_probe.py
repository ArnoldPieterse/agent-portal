import winrm, re
HOSTS = {'PALE': ('IP_PALE', 'pale'), 'BLACK': ('IP_BLACK', 'black'), 'RED': ('IP_RED', 'red')}
for host, (ip, user) in HOSTS.items():
    s = winrm.Session('http://' + ip + ':5985/wsman', auth=(user, ''), transport='ntlm',
                      operation_timeout_sec=60, read_timeout_sec=180)
    r = s.run_cmd('cmd', ['/c', 'netstat -ano | findstr :8888'])
    pids = set(re.findall(r'LISTENING\s+(\d+)\s*$', r.std_out.decode().replace(chr(13),''), re.M))
    paths = []
    for pid in list(pids)[:2]:
        r2 = s.run_cmd('powershell', ['-NoProfile', '-Command', 'Get-Process -Id ' + pid + ' | Select-Object -ExpandProperty Path'])
        pth = r2.std_out.decode().strip()
        if pth: paths.append(pth)
    print(host, paths[:1])
