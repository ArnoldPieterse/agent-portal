import winrm, re, json, base64, datetime
HOSTS = {'PALE': ('IP_PALE', 'pale'), 'BLACK': ('IP_BLACK', 'black'), 'RED': ('IP_RED', 'red')}
LOG = 'memory/mechanic/reboot-recovery.jsonl'
PS1 = """$ErrorActionPreference = 'SilentlyContinue'
$log = 'C:/FleetOps/watchdog.log'
function Log($m) { Add-Content -Path $log -Value ((Get-Date).ToString('s') + ' ' + $m) }
$listen = netstat -ano | Select-String ':8888\s+.*LISTENING'
if ($listen) { exit 0 }
Log 'port 8888 down -> launching studio'
$line = (Get-Content C:/FleetOps/studio_launch.txt -Raw).Trim()
Start-Process -FilePath cmd.exe -ArgumentList '/c', $line -WindowStyle Hidden
Log 'launch issued'
"""
def put(s, remote_path, content):
    b = base64.b64encode(content.encode('utf-8')).decode()
    ps = ("Remove-Item C:/FleetOps/x.b64, " + remote_path + " -ErrorAction SilentlyContinue; "
          "Set-Content -Path C:/FleetOps/x.b64 -Value '" + b + "' -Encoding ASCII; certutil -decode C:/FleetOps/x.b64 " + remote_path)
    r = s.run_ps(ps)
    return 'successfully' in (r.std_out.decode() + r.std_err.decode())
def log_entry(e):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(e) + '\n')
for host, (ip, user) in HOSTS.items():
    e = {'ts': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'host': host,
         'type': 'deploy_watchdog_remote', 'ok': False}
    try:
        s = winrm.Session('http://' + ip + ':5985/wsman', auth=(user, ''), transport='ntlm',
                          operation_timeout_sec=60, read_timeout_sec=180)
        s.run_cmd('cmd', ['/c', 'mkdir C:/FleetOps 2>nul'])
        launcher = open('memory/mechanic/launcher_' + host + '.txt', encoding='utf-8').read().strip()
        e['files'] = [put(s, 'C:/FleetOps/studio_launch.txt', launcher), put(s, 'C:/FleetOps/fleet_watchdog.ps1', PS1)]
        psreg = ('$a = New-ScheduledTaskAction -Execute powershell.exe '
                 "-Argument '-NoProfile -ExecutionPolicy Bypass -File C:/FleetOps/fleet_watchdog.ps1'; "
                 '$t = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5); '
                 'Register-ScheduledTask -TaskName FleetBootRecovery -Action $a -Trigger $t -Force | Out-Null; '
                 '(Get-ScheduledTask FleetBootRecovery).State')
        r = s.run_ps(psreg)
        e['task_user'] = (r.std_out.decode() + r.std_err.decode()).strip()[:80]
        v = s.run_cmd('schtasks', ['/query', '/tn', 'FleetBootRecovery', '/fo', 'csv', '/nh'])
        e['verified'] = v.status_code == 0 and 'FleetBootRecovery' in v.std_out.decode()
        e['ok'] = all(e['files']) and e['verified']
    except Exception as ex:
        e['error'] = str(ex)[:150]
    log_entry(e)
print('done')