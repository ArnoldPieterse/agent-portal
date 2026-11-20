"""Register FleetBootRecovery on PALE/BLACK/RED via WinRM (empty-pw fleet rule).
Copies reboot_recover.py to C:/FleetOps and creates a boot-recovery task
(onstart/SYSTEM first; falls back to user 5-min watchdog). Logs JSONL evidence."""
import winrm, json, base64, datetime, pathlib

HOSTS = {
    'PALE': ('IP_PALE', 'pale'),
    'BLACK': ('IP_BLACK', 'black'),
    'RED': ('IP_RED', 'red'),
}
SRC = pathlib.Path(__file__).parent / 'reboot_recover.py'
LOG = pathlib.Path(__file__).parent / 'reboot-recovery.jsonl'

def log_entry(e):
    with open(LOG, 'a') as f:
        f.write(json.dumps(e) + chr(10))

src_b64 = base64.b64encode(SRC.read_bytes()).decode()

for host, (ip, user) in HOSTS.items():
    entry = {'ts': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'host': host, 'type': 'deploy_reboot_recovery_winrm'}
    try:
        s = winrm.Session('http://' + ip + ':5985/wsman', auth=(user, ''), transport='ntlm',
                          operation_timeout_sec=60, read_timeout_sec=180)
        # locate a real python (skip WindowsApps store stub)
        cands = ['C:/Python312/python.exe', 'C:/Python311/python.exe',
                 'C:/Python310/python.exe', 'C:/Python/python.exe',
                 'C:/Users/' + user + '/AppData/Local/Programs/Python/Python312/python.exe',
                 'C:/Users/' + user + '/AppData/Local/Programs/Python/Python311/python.exe',
                 'C:/Projects/Workspace/Python/pythoncore-3.15-64/python.exe']
        probe = 'for %P in (' + ' '.join(cands) + ') do @if exist %P @echo FOUND %P'
        r = s.run_cmd('cmd', ['/c', probe])
        found = [l for l in r.std_out.decode().splitlines() if l.startswith('FOUND')]
        py = found[0].split('FOUND ')[1] if found else None
        entry['python'] = py
        if not py:
            entry.update(ok=False, error='no real python found on remote')
            log_entry(entry); continue
        # copy script (b64 -> certutil decode)
        s.run_cmd('cmd', ['/c', 'mkdir C:/FleetOps 2>nul'])
        ps = "Set-Content -Path C:/FleetOps/reboot_recover.b64 -Value '" + src_b64 + "' -NoNewline"
        s.run_cmd('powershell', ['-NoProfile', '-Command', ps])
        r = s.run_cmd('certutil', ['-decode', 'C:/FleetOps/reboot_recover.b64', 'C:/FleetOps/reboot_recover.py'])
        entry['copy'] = 'OK' if r.status_code == 0 else 'FAIL ' + r.std_err.decode()[:120]
        # register task: onstart SYSTEM first (remote user is local admin)
        tr = '"' + py + '" "C:/FleetOps/reboot_recover.py"'
        r = s.run_cmd('schtasks', ['/create', '/tn', 'FleetBootRecovery', '/tr', tr,
                                   '/sc', 'onstart', '/ru', 'SYSTEM', '/rl', 'HIGHEST', '/f'])
        if r.status_code == 0:
            entry['task'] = 'onstart SYSTEM'
        else:
            r2 = s.run_cmd('schtasks', ['/create', '/tn', 'FleetBootRecovery', '/tr', tr,
                                        '/sc', 'minute', '/mo', '5', '/ru', user, '/f'])
            entry['task'] = ('5-min user' if r2.status_code == 0
                             else 'BOTH-FAILED: ' + r.std_err.decode()[:100] + ' / ' + r2.std_err.decode()[:100])
        q = s.run_cmd('schtasks', ['/query', '/tn', 'FleetBootRecovery', '/fo', 'CSV', '/nh'])
        entry['verified'] = 'FleetBootRecovery' in q.std_out.decode()
        entry['ok'] = (entry['copy'] == 'OK') and entry['verified']
    except Exception as e:
        entry.update(ok=False, error=str(e)[:200])
    log_entry(entry)
    print(host, json.dumps({k: v for k, v in entry.items() if k != "ts"}))

print('Done. Evidence ->', LOG)
