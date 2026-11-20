import winrm
HOSTS = {'PALE': ('IP_PALE', 'pale'), 'BLACK': ('IP_BLACK', 'black'), 'RED': ('IP_RED', 'red')}
for host, (ip, user) in HOSTS.items():
    s = winrm.Session('http://' + ip + ':5985/wsman', auth=(user, ''), transport='ntlm',
                      operation_timeout_sec=60, read_timeout_sec=180)
    r1 = s.run_cmd('cmd', ['/c', 'dir /s /b C:/Users/' + user + '/.unsloth 2>nul'])
    d1 = r1.std_out.decode().strip()[:300]
    r2 = s.run_cmd('cmd', ['/c', 'netstat -ano | findstr :8888'])
    d2 = r2.std_out.decode().strip()[:150]
    r3 = s.run_cmd('cmd', ['/c', 'dir /b C:/Users/' + user + '/AppData/Local 2>nul | findstr -i unsloth'])
    d3 = r3.std_out.decode().strip()[:150]
    verdict = {'unsloth': bool(d1), 'port8888': bool(d2), 'appdata': len(d3)}
    print(host, verdict)
