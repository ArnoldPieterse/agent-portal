import winrm, re
HOSTS = {'PALE': ('IP_PALE', 'pale'), 'BLACK': ('IP_BLACK', 'black'), 'RED': ('IP_RED', 'red')}
for host, (ip, user) in HOSTS.items():
    s = winrm.Session('http://' + ip + ':5985/wsman', auth=(user, ''), transport='ntlm',
                      operation_timeout_sec=60, read_timeout_sec=180)
    r = s.run_cmd('cmd', ['/c', 'netstat -ano | findstr :8888'])
    m = re.search(r'LISTENING\s+(\d+)', r.std_out.decode().replace(chr(13), ''))
    pid = m.group(1) if m else None
    out = s.run_ps('Get-CimInstance Win32_Process -Filter "ProcessId=' + str(pid) + '" | Select-Object -ExpandProperty CommandLine').std_out.decode().strip()
    print(host, pid, out[:150])
