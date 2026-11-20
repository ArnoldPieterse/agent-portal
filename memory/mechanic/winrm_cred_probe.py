"""Probe WinRM creds on PALE/BLACK/RED: empty pw first (fleet rule 11-18), then legacy."""
import winrm, json

HOSTS = {'PALE': ('IP_PALE', 'pale'), 'BLACK': ('IP_BLACK', 'black'), 'RED': ('IP_RED', 'red')}
PWS = ['', '[REDACTED-CREDENTIAL]']

out = {}
for host, (ip, user) in HOSTS.items():
    for pw in PWS:
        try:
            s = winrm.Session(f'http://{ip}:5985/wsman', auth=(user, pw), transport='ntlm', operation_timeout_sec=15)
            r = s.run_cmd('whoami')
            out[host] = {'pw': repr(pw), 'ok': True, 'whoami': r.std_out.decode().strip()}
            break
        except Exception as e:
            err = str(e)[:80]
            if pw == PWS[-1]:
                out[host] = {'ok': False, 'err': err}
print(json.dumps(out, indent=1))
